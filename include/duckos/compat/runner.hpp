#pragma once

#include "duckos/compat/pe_image.hpp"
#include "duckos/compat/prefix_manager.hpp"

#include <filesystem>
#include <string>
#include <vector>

namespace duckos::compat {

struct RunOptions {
    std::filesystem::path executable;
    std::filesystem::path compat_root;
    std::string prefix_id;
    std::vector<std::string> arguments;
};

bool command_available(const std::string& command);
int initialise_wine_prefix(const PrefixInfo& prefix);
int run_windows_program(const RunOptions& options, const PeImageInfo& image);
void print_diagnostics(const std::filesystem::path& compat_root);

} // namespace duckos::compat
