#include "duckos/compat/pe_image.hpp"

#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

namespace {

void put16(std::vector<std::uint8_t>& bytes, std::size_t offset, std::uint16_t value) {
    bytes.at(offset) = static_cast<std::uint8_t>(value & 0xffU);
    bytes.at(offset + 1) = static_cast<std::uint8_t>((value >> 8U) & 0xffU);
}

void put32(std::vector<std::uint8_t>& bytes, std::size_t offset, std::uint32_t value) {
    for (unsigned i = 0; i < 4; ++i) {
        bytes.at(offset + i) = static_cast<std::uint8_t>((value >> (i * 8U)) & 0xffU);
    }
}

std::vector<std::uint8_t> make_pe(std::uint16_t machine, std::uint16_t magic) {
    std::vector<std::uint8_t> bytes(0x400, 0);
    put16(bytes, 0, 0x5a4d);
    put32(bytes, 0x3c, 0x80);
    put32(bytes, 0x80, 0x00004550);
    put16(bytes, 0x84, machine);
    put16(bytes, 0x86, 1);
    put16(bytes, 0x94, magic == 0x20b ? 0xf0 : 0xe0);
    put16(bytes, 0x96, 0x0002);

    const std::size_t optional = 0x98;
    put16(bytes, optional, magic);
    put32(bytes, optional + 16, 0x1000);
    put32(bytes, optional + 56, 0x2000);
    put32(bytes, optional + 60, 0x200);
    put16(bytes, optional + 68, 3);
    put32(bytes, optional + (magic == 0x20b ? 108 : 92), 16);

    const std::size_t section = optional + (magic == 0x20b ? 0xf0 : 0xe0);
    put32(bytes, section + 8, 0x200);
    put32(bytes, section + 12, 0x1000);
    put32(bytes, section + 16, 0x200);
    put32(bytes, section + 20, 0x200);
    return bytes;
}

std::filesystem::path write_fixture(const std::string& name, const std::vector<std::uint8_t>& bytes) {
    const auto path = std::filesystem::temp_directory_path() / ("duckos-pe-" + name + ".bin");
    std::ofstream output(path, std::ios::binary | std::ios::trunc);
    output.write(reinterpret_cast<const char*>(bytes.data()), static_cast<std::streamsize>(bytes.size()));
    if (!output) throw std::runtime_error("could not write test fixture");
    return path;
}

void expect(bool condition, const std::string& message) {
    if (!condition) throw std::runtime_error(message);
}

void test_valid_pe32_plus() {
    const auto path = write_fixture("valid64", make_pe(0x8664, 0x20b));
    const auto info = duckos::compat::inspect_pe(path);
    expect(info.architecture == duckos::compat::PeArchitecture::x86_64, "x64 architecture was not detected");
    expect(info.kind == duckos::compat::PeKind::pe32_plus, "PE32+ kind was not detected");
    expect(info.subsystem == duckos::compat::PeSubsystem::windows_console, "console subsystem was not detected");
    expect(info.entry_point_rva == 0x1000, "entry point was parsed incorrectly");
    std::filesystem::remove(path);
}

void test_valid_pe32() {
    const auto path = write_fixture("valid32", make_pe(0x014c, 0x10b));
    const auto info = duckos::compat::inspect_pe(path);
    expect(info.architecture == duckos::compat::PeArchitecture::x86, "x86 architecture was not detected");
    expect(info.kind == duckos::compat::PeKind::pe32, "PE32 kind was not detected");
    std::filesystem::remove(path);
}

void test_import_table() {
    auto bytes = make_pe(0x8664, 0x20b);
    const std::size_t optional = 0x98;
    const std::size_t directories = optional + 112;
    put32(bytes, directories + 8, 0x1100);
    put32(bytes, directories + 12, 40);
    put32(bytes, 0x300 + 12, 0x1040);
    put32(bytes, 0x300 + 16, 0x1200);
    const std::string name = "KERNEL32.dll";
    for (std::size_t i = 0; i < name.size(); ++i) {
        bytes[0x240 + i] = static_cast<std::uint8_t>(name[i]);
    }
    const auto path = write_fixture("imports", bytes);
    const auto info = duckos::compat::inspect_pe(path);
    expect(info.imports.size() == 1, "import table was not enumerated");
    expect(info.imports.front() == "KERNEL32.dll", "imported DLL name was parsed incorrectly");
    std::filesystem::remove(path);
}

void test_rejects_non_pe() {
    const auto path = write_fixture("notpe", std::vector<std::uint8_t>(128, 0));
    bool rejected = false;
    try {
        (void)duckos::compat::inspect_pe(path);
    } catch (const duckos::compat::PeFormatError&) {
        rejected = true;
    }
    std::filesystem::remove(path);
    expect(rejected, "non-PE file should be rejected");
}

void test_rejects_bitness_mismatch() {
    const auto path = write_fixture("mismatch", make_pe(0x8664, 0x10b));
    bool rejected = false;
    try {
        (void)duckos::compat::inspect_pe(path);
    } catch (const duckos::compat::PeFormatError&) {
        rejected = true;
    }
    std::filesystem::remove(path);
    expect(rejected, "machine/optional-header bitness mismatch should be rejected");
}

} // namespace

int main() {
    try {
        test_valid_pe32_plus();
        test_valid_pe32();
        test_import_table();
        test_rejects_non_pe();
        test_rejects_bitness_mismatch();
        std::cout << "All PE inspection tests passed.\n";
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "Test failure: " << error.what() << '\n';
        return 1;
    }
}
