#pragma once

#include <filesystem>
#include <string>

namespace duckos::compat {

enum class LaunchProfile {
    utility,
    retro,
    modern
};

struct PrefixInfo {
    std::string id;
    std::filesystem::path root;
    std::filesystem::path wine_prefix;
    std::filesystem::path logs;
    std::filesystem::path snapshots;
    std::string wine_arch{"win64"};
    LaunchProfile profile{LaunchProfile::utility};
};

std::filesystem::path default_compat_root();
std::string profile_name(LaunchProfile profile);
LaunchProfile parse_profile(const std::string& value);
PrefixInfo create_prefix_layout(const std::filesystem::path& compat_root,
                                const std::string& id,
                                const std::string& wine_arch,
                                LaunchProfile profile);
PrefixInfo open_prefix_layout(const std::filesystem::path& compat_root,
                               const std::string& id);

} // namespace duckos::compat
