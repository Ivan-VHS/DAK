#include "duckos/compat/pe_image.hpp"

#include <algorithm>
#include <array>
#include <fstream>
#include <limits>
#include <system_error>

namespace duckos::compat {
namespace {

constexpr std::uint64_t max_image_size = 512ULL * 1024ULL * 1024ULL;
constexpr std::uint16_t machine_i386 = 0x014c;
constexpr std::uint16_t machine_amd64 = 0x8664;
constexpr std::uint16_t machine_arm64 = 0xaa64;
constexpr std::uint16_t optional_pe32 = 0x010b;
constexpr std::uint16_t optional_pe32_plus = 0x020b;
constexpr std::uint32_t import_directory_index = 1;
constexpr std::uint32_t relocation_directory_index = 5;

struct Section {
    std::uint32_t virtual_address{};
    std::uint32_t virtual_size{};
    std::uint32_t raw_offset{};
    std::uint32_t raw_size{};
};

class ImageBytes {
public:
    explicit ImageBytes(const std::filesystem::path& file) {
        std::ifstream input(file, std::ios::binary | std::ios::ate);
        if (!input) {
            throw PeFormatError("cannot open file: " + file.string());
        }

        const auto end = input.tellg();
        if (end < 0) {
            throw PeFormatError("cannot determine file size: " + file.string());
        }
        const auto size = static_cast<std::uint64_t>(end);
        if (size < 64 || size > max_image_size) {
            throw PeFormatError("file size is outside the supported PE inspection range");
        }

        bytes_.resize(static_cast<std::size_t>(size));
        input.seekg(0, std::ios::beg);
        if (!input.read(reinterpret_cast<char*>(bytes_.data()), static_cast<std::streamsize>(bytes_.size()))) {
            throw PeFormatError("failed to read complete file: " + file.string());
        }
    }

    std::size_t size() const noexcept { return bytes_.size(); }

    void require(std::uint64_t offset, std::uint64_t length, const char* what) const {
        if (offset > bytes_.size() || length > bytes_.size() - offset) {
            throw PeFormatError(std::string("truncated PE image while reading ") + what);
        }
    }

    std::uint16_t u16(std::uint64_t offset, const char* what) const {
        require(offset, 2, what);
        return static_cast<std::uint16_t>(bytes_[offset]) |
               (static_cast<std::uint16_t>(bytes_[offset + 1]) << 8U);
    }

    std::uint32_t u32(std::uint64_t offset, const char* what) const {
        require(offset, 4, what);
        return static_cast<std::uint32_t>(bytes_[offset]) |
               (static_cast<std::uint32_t>(bytes_[offset + 1]) << 8U) |
               (static_cast<std::uint32_t>(bytes_[offset + 2]) << 16U) |
               (static_cast<std::uint32_t>(bytes_[offset + 3]) << 24U);
    }

    std::string c_string(std::uint64_t offset, std::size_t limit, const char* what) const {
        require(offset, 1, what);
        const auto available = std::min<std::uint64_t>(limit, bytes_.size() - offset);
        std::string value;
        value.reserve(static_cast<std::size_t>(std::min<std::uint64_t>(available, 128)));
        for (std::uint64_t i = 0; i < available; ++i) {
            const char ch = static_cast<char>(bytes_[offset + i]);
            if (ch == '\0') {
                return value;
            }
            value.push_back(ch);
        }
        throw PeFormatError(std::string("unterminated string in PE image: ") + what);
    }

private:
    std::vector<std::uint8_t> bytes_;
};

std::uint64_t checked_add(std::uint64_t left, std::uint64_t right, const char* what) {
    if (right > std::numeric_limits<std::uint64_t>::max() - left) {
        throw PeFormatError(std::string("integer overflow while reading ") + what);
    }
    return left + right;
}

std::uint64_t rva_to_offset(const ImageBytes& image,
                            std::uint32_t rva,
                            const std::vector<Section>& sections,
                            std::uint32_t size_of_headers,
                            const char* what) {
    if (rva < size_of_headers) {
        image.require(rva, 1, what);
        return rva;
    }

    for (const auto& section : sections) {
        const auto mapped_size = std::max(section.virtual_size, section.raw_size);
        const std::uint64_t start = section.virtual_address;
        const std::uint64_t end = start + mapped_size;
        if (rva >= start && static_cast<std::uint64_t>(rva) < end) {
            const auto delta = static_cast<std::uint64_t>(rva) - start;
            if (delta >= section.raw_size) {
                throw PeFormatError(std::string("RVA points to uninitialized section data: ") + what);
            }
            const auto offset = checked_add(section.raw_offset, delta, what);
            image.require(offset, 1, what);
            return offset;
        }
    }

    throw PeFormatError(std::string("RVA is not mapped by any PE section: ") + what);
}

PeArchitecture architecture_from_machine(std::uint16_t machine) noexcept {
    switch (machine) {
    case machine_i386: return PeArchitecture::x86;
    case machine_amd64: return PeArchitecture::x86_64;
    case machine_arm64: return PeArchitecture::arm64;
    default: return PeArchitecture::unknown;
    }
}

PeSubsystem subsystem_from_value(std::uint16_t value) noexcept {
    switch (value) {
    case 1: return PeSubsystem::native;
    case 2: return PeSubsystem::windows_gui;
    case 3: return PeSubsystem::windows_console;
    case 7: return PeSubsystem::posix_console;
    case 10: return PeSubsystem::efi_application;
    default: return PeSubsystem::unknown;
    }
}

} // namespace

PeImageInfo inspect_pe(const std::filesystem::path& file) {
    ImageBytes image(file);
    if (image.u16(0, "DOS signature") != 0x5a4d) {
        throw PeFormatError("file does not have an MZ DOS signature");
    }

    const auto pe_offset = image.u32(0x3c, "e_lfanew");
    image.require(pe_offset, 24, "PE and COFF headers");
    if (image.u32(pe_offset, "PE signature") != 0x00004550) {
        throw PeFormatError("MZ file does not contain a valid PE signature");
    }

    const auto coff = static_cast<std::uint64_t>(pe_offset) + 4;
    const auto machine = image.u16(coff, "COFF machine");
    const auto section_count = image.u16(coff + 2, "section count");
    const auto optional_size = image.u16(coff + 16, "optional-header size");
    const auto characteristics = image.u16(coff + 18, "COFF characteristics");
    if (section_count > 96) {
        throw PeFormatError("PE image declares more than 96 sections");
    }

    const auto optional = coff + 20;
    image.require(optional, optional_size, "optional header");
    const auto magic = image.u16(optional, "optional-header magic");
    PeKind kind;
    std::uint32_t directory_count_offset;
    std::uint32_t directory_table_offset;
    if (magic == optional_pe32) {
        kind = PeKind::pe32;
        directory_count_offset = 92;
        directory_table_offset = 96;
    } else if (magic == optional_pe32_plus) {
        kind = PeKind::pe32_plus;
        directory_count_offset = 108;
        directory_table_offset = 112;
    } else {
        throw PeFormatError("unsupported PE optional-header magic");
    }

    const auto architecture = architecture_from_machine(machine);
    if ((architecture == PeArchitecture::x86 && kind != PeKind::pe32) ||
        ((architecture == PeArchitecture::x86_64 || architecture == PeArchitecture::arm64) && kind != PeKind::pe32_plus)) {
        throw PeFormatError("COFF machine and optional-header bitness do not match");
    }

    if (optional_size < 70 || optional_size < directory_count_offset + 4) {
        throw PeFormatError("optional header is too short");
    }

    const auto entry_point = image.u32(optional + 16, "entry point RVA");
    const auto image_size = image.u32(optional + 56, "SizeOfImage");
    const auto size_of_headers = image.u32(optional + 60, "SizeOfHeaders");
    const auto subsystem = image.u16(optional + 68, "subsystem");
    const auto directory_count = image.u32(optional + directory_count_offset, "data-directory count");

    const auto section_table = optional + optional_size;
    image.require(section_table, static_cast<std::uint64_t>(section_count) * 40, "section table");
    std::vector<Section> sections;
    sections.reserve(section_count);
    for (std::uint16_t i = 0; i < section_count; ++i) {
        const auto offset = section_table + static_cast<std::uint64_t>(i) * 40;
        sections.push_back(Section{
            image.u32(offset + 12, "section virtual address"),
            image.u32(offset + 8, "section virtual size"),
            image.u32(offset + 20, "section raw offset"),
            image.u32(offset + 16, "section raw size")
        });
    }

    const auto directory_offset = optional + directory_table_offset;
    const auto read_directory = [&](std::uint32_t index) -> std::pair<std::uint32_t, std::uint32_t> {
        if (index >= directory_count || directory_offset + (static_cast<std::uint64_t>(index) + 1) * 8 > optional + optional_size) {
            return {0, 0};
        }
        const auto offset = directory_offset + static_cast<std::uint64_t>(index) * 8;
        return {image.u32(offset, "data-directory RVA"), image.u32(offset + 4, "data-directory size")};
    };

    PeImageInfo info;
    info.file = file;
    info.architecture = architecture;
    info.kind = kind;
    info.subsystem = subsystem_from_value(subsystem);
    info.image_size = image_size;
    info.entry_point_rva = entry_point;
    info.is_dll = (characteristics & 0x2000U) != 0;
    info.has_relocations = read_directory(relocation_directory_index).first != 0;

    const auto [import_rva, import_size] = read_directory(import_directory_index);
    if (import_rva != 0 && import_size != 0) {
        const auto import_offset = rva_to_offset(image, import_rva, sections, size_of_headers, "import directory");
        const auto descriptor_count = std::min<std::uint64_t>(import_size / 20, 4096);
        for (std::uint64_t i = 0; i < descriptor_count; ++i) {
            const auto descriptor = import_offset + i * 20;
            image.require(descriptor, 20, "import descriptor");
            const auto original_thunk = image.u32(descriptor, "OriginalFirstThunk");
            const auto time_date_stamp = image.u32(descriptor + 4, "import timestamp");
            const auto forwarder_chain = image.u32(descriptor + 8, "import forwarder chain");
            const auto name_rva = image.u32(descriptor + 12, "import module name RVA");
            const auto first_thunk = image.u32(descriptor + 16, "FirstThunk");
            if (original_thunk == 0 && time_date_stamp == 0 && forwarder_chain == 0 && name_rva == 0 && first_thunk == 0) {
                break;
            }
            if (name_rva == 0) {
                throw PeFormatError("import descriptor has no module name");
            }
            const auto name_offset = rva_to_offset(image, name_rva, sections, size_of_headers, "import module name");
            auto module = image.c_string(name_offset, 260, "import module name");
            if (module.empty()) {
                throw PeFormatError("import descriptor contains an empty module name");
            }
            info.imports.push_back(std::move(module));
        }
    }

    std::sort(info.imports.begin(), info.imports.end());
    info.imports.erase(std::unique(info.imports.begin(), info.imports.end()), info.imports.end());
    return info;
}

const char* to_string(PeArchitecture architecture) noexcept {
    switch (architecture) {
    case PeArchitecture::x86: return "x86";
    case PeArchitecture::x86_64: return "x86_64";
    case PeArchitecture::arm64: return "arm64";
    default: return "unknown";
    }
}

const char* to_string(PeKind kind) noexcept {
    return kind == PeKind::pe32 ? "PE32" : "PE32+";
}

const char* to_string(PeSubsystem subsystem) noexcept {
    switch (subsystem) {
    case PeSubsystem::native: return "native";
    case PeSubsystem::windows_gui: return "windows-gui";
    case PeSubsystem::windows_console: return "windows-console";
    case PeSubsystem::posix_console: return "posix-console";
    case PeSubsystem::efi_application: return "efi-application";
    default: return "unknown";
    }
}

} // namespace duckos::compat
