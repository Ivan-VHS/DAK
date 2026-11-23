#pragma once

#include <cstdint>
#include <filesystem>
#include <stdexcept>
#include <string>
#include <vector>

namespace duckos::compat {

enum class PeArchitecture {
    x86,
    x86_64,
    arm64,
    unknown
};

enum class PeKind {
    pe32,
    pe32_plus
};

enum class PeSubsystem {
    unknown,
    native,
    windows_gui,
    windows_console,
    posix_console,
    efi_application
};

struct PeImageInfo {
    std::filesystem::path file;
    PeArchitecture architecture{PeArchitecture::unknown};
    PeKind kind{PeKind::pe32};
    PeSubsystem subsystem{PeSubsystem::unknown};
    std::uint32_t image_size{};
    std::uint32_t entry_point_rva{};
    bool is_dll{};
    bool has_relocations{};
    std::vector<std::string> imports;
};

class PeFormatError : public std::runtime_error {
public:
    using std::runtime_error::runtime_error;
};

PeImageInfo inspect_pe(const std::filesystem::path& file);
const char* to_string(PeArchitecture architecture) noexcept;
const char* to_string(PeKind kind) noexcept;
const char* to_string(PeSubsystem subsystem) noexcept;

} // namespace duckos::compat
