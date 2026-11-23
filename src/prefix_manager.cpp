#include "duckos/compat/prefix_manager.hpp"

#include <cctype>
#include <cstdlib>
#include <fstream>
#include <stdexcept>
#include <string_view>
#include <system_error>

#ifndef _WIN32
#include <sys/stat.h>
#endif

namespace duckos::compat {
namespace {

bool valid_id(const std::string& id) {
    if (id.empty() || id.size() > 64 || id == "." || id == "..") {
        return false;
    }
    for (const unsigned char ch : id) {
        if (!(std::isalnum(ch) || ch == '-' || ch == '_')) {
            return false;
        }
    }
    return true;
}

void ensure_directory(const std::filesystem::path& path) {
    std::error_code error;
    std::filesystem::create_directories(path, error);
    if (error) {
        throw std::runtime_error("cannot create directory '" + path.string() + "': " + error.message());
    }
#ifndef _WIN32
    if (::chmod(path.c_str(), S_IRWXU) != 0) {
        throw std::runtime_error("cannot restrict directory permissions: " + path.string());
    }
#endif
}

std::string toml_quote(const std::string& value) {
    std::string escaped;
    escaped.reserve(value.size() + 2);
    escaped.push_back('"');
    for (const char ch : value) {
        if (ch == '\\' || ch == '"') {
            escaped.push_back('\\');
        }
        if (ch == '\n' || ch == '\r') {
            escaped.push_back(' ');
        } else {
            escaped.push_back(ch);
        }
    }
    escaped.push_back('"');
    return escaped;
}

PrefixInfo make_info(const std::filesystem::path& root,
                     const std::string& id,
                     const std::string& wine_arch,
                     LaunchProfile profile) {
    PrefixInfo info;
    info.id = id;
    info.root = root;
    info.wine_prefix = root / "wine";
    info.logs = root / "logs";
    info.snapshots = root / "snapshots";
    info.wine_arch = wine_arch;
    info.profile = profile;
    return info;
}

} // namespace

std::filesystem::path default_compat_root() {
    if (const char* xdg = std::getenv("XDG_DATA_HOME"); xdg != nullptr && *xdg != '\0') {
        return std::filesystem::path(xdg) / "duckos" / "compat";
    }
    if (const char* home = std::getenv("HOME"); home != nullptr && *home != '\0') {
        return std::filesystem::path(home) / ".local" / "share" / "duckos" / "compat";
    }
    return std::filesystem::current_path() / ".duckos-compat";
}

std::string profile_name(LaunchProfile profile) {
    switch (profile) {
    case LaunchProfile::utility: return "utility";
    case LaunchProfile::retro: return "retro";
    case LaunchProfile::modern: return "modern";
    }
    return "utility";
}

LaunchProfile parse_profile(const std::string& value) {
    if (value == "utility") return LaunchProfile::utility;
    if (value == "retro") return LaunchProfile::retro;
    if (value == "modern") return LaunchProfile::modern;
    throw std::invalid_argument("unknown profile '" + value + "' (use utility, retro or modern)");
}

PrefixInfo create_prefix_layout(const std::filesystem::path& compat_root,
                                const std::string& id,
                                const std::string& wine_arch,
                                LaunchProfile profile) {
    if (!valid_id(id)) {
        throw std::invalid_argument("prefix ID must contain 1-64 letters, digits, '-' or '_'");
    }
    if (wine_arch != "win32" && wine_arch != "win64") {
        throw std::invalid_argument("Wine architecture must be win32 or win64");
    }

    const auto root = compat_root / "prefixes" / id;
    if (std::filesystem::exists(root / "prefix.toml")) {
        throw std::runtime_error("prefix already exists: " + id);
    }

    ensure_directory(root);
    ensure_directory(root / "wine");
    ensure_directory(root / "cache" / "shaders");
    ensure_directory(root / "logs");
    ensure_directory(root / "snapshots");

    const auto config = root / "prefix.toml";
    const auto temporary = root / "prefix.toml.tmp";
    {
        std::ofstream output(temporary, std::ios::binary | std::ios::trunc);
        if (!output) {
            throw std::runtime_error("cannot write prefix configuration: " + temporary.string());
        }
        output << "# DuckOS compatibility prefix v1\n"
               << "[prefix]\n"
               << "id = " << toml_quote(id) << "\n"
               << "wine_arch = " << toml_quote(wine_arch) << "\n"
               << "profile = " << toml_quote(profile_name(profile)) << "\n"
               << "backend = \"wine\"\n"
               << "graphics = \"auto\"\n"
               << "sandbox = \"none\"\n"
               << "prefix_isolation = \"wine-user-prefix\"\n"
               << "network = \"host-default\"\n"
               << "anticheat = \"not-guaranteed\"\n";
        output.flush();
        if (!output) {
            throw std::runtime_error("failed to finish prefix configuration: " + temporary.string());
        }
    }

    std::error_code error;
    std::filesystem::rename(temporary, config, error);
    if (error) {
        throw std::runtime_error("cannot publish prefix configuration: " + error.message());
    }
    return make_info(root, id, wine_arch, profile);
}

PrefixInfo open_prefix_layout(const std::filesystem::path& compat_root, const std::string& id) {
    if (!valid_id(id)) {
        throw std::invalid_argument("prefix ID must contain 1-64 letters, digits, '-' or '_'");
    }
    const auto root = compat_root / "prefixes" / id;
    const auto config = root / "prefix.toml";
    if (!std::filesystem::is_regular_file(config)) {
        throw std::runtime_error("prefix does not exist: " + id);
    }

    std::ifstream input(config);
    if (!input) {
        throw std::runtime_error("cannot read prefix configuration: " + config.string());
    }
    std::string arch = "win64";
    std::string profile = "utility";
    std::string line;
    while (std::getline(input, line)) {
        const auto separator = line.find('=');
        if (separator == std::string::npos) continue;
        const auto key_start = line.find_first_not_of(" \t");
        const auto key_end = line.find_last_not_of(" \t", separator - 1);
        if (key_start == std::string::npos || key_end == std::string::npos) continue;
        const auto key = line.substr(key_start, key_end - key_start + 1);
        const auto quote_start = line.find('"', separator + 1);
        if (quote_start == std::string::npos) continue;
        const auto quote_end = line.find('"', quote_start + 1);
        if (quote_end == std::string::npos) continue;
        const auto value = line.substr(quote_start + 1, quote_end - quote_start - 1);
        if (key == "wine_arch") arch = value;
        if (key == "profile") profile = value;
    }
    if (arch != "win32" && arch != "win64") {
        throw std::runtime_error("prefix has an invalid wine_arch value: " + arch);
    }
    return make_info(root, id, arch, parse_profile(profile));
}

} // namespace duckos::compat
