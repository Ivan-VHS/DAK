#include "duckos/compat/prefix_manager.hpp"

#include <filesystem>
#include <iostream>
#include <stdexcept>
#include <string>

namespace {

void expect(bool condition, const std::string& message) {
    if (!condition) throw std::runtime_error(message);
}

void test_prefix_round_trip() {
    const auto root = std::filesystem::temp_directory_path() / "duckos-prefix-test-root";
    std::filesystem::remove_all(root);

    const auto created = duckos::compat::create_prefix_layout(
        root, "test-game", "win64", duckos::compat::LaunchProfile::modern);
    expect(std::filesystem::is_directory(created.wine_prefix), "Wine prefix directory was not created");
    expect(std::filesystem::is_directory(created.logs), "log directory was not created");
    expect(std::filesystem::is_regular_file(created.root / "prefix.toml"), "prefix config was not created");

    const auto reopened = duckos::compat::open_prefix_layout(root, "test-game");
    expect(reopened.wine_arch == "win64", "Wine architecture did not survive config round trip");
    expect(reopened.profile == duckos::compat::LaunchProfile::modern, "launch profile did not survive config round trip");

    std::filesystem::remove_all(root);
}

void test_prefix_id_cannot_escape_root() {
    const auto root = std::filesystem::temp_directory_path() / "duckos-prefix-test-traversal";
    bool rejected = false;
    try {
        (void)duckos::compat::create_prefix_layout(root, "../outside", "win64", duckos::compat::LaunchProfile::utility);
    } catch (const std::invalid_argument&) {
        rejected = true;
    }
    std::filesystem::remove_all(root);
    expect(rejected, "path traversal prefix ID should be rejected");
}

} // namespace

int main() {
    try {
        test_prefix_round_trip();
        test_prefix_id_cannot_escape_root();
        std::cout << "All prefix manager tests passed.\n";
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "Test failure: " << error.what() << '\n';
        return 1;
    }
}
