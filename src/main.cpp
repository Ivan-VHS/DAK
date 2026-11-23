#include "duckos/compat/pe_image.hpp"
#include "duckos/compat/prefix_manager.hpp"
#include "duckos/compat/runner.hpp"

#include <algorithm>
#include <cctype>
#include <filesystem>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

namespace {

void print_usage() {
    std::cout << R"(DuckOS Windows compatibility runner

Usage:
  os-run inspect <file.exe>
  os-run doctor [--root PATH]
  os-run prefix create <id> [--arch win32|win64] [--profile utility|retro|modern] [--root PATH]
  os-run run <file.exe> [--prefix ID] [--arch win32|win64] [--profile utility|retro|modern] [--root PATH] [-- ARG...]

Profiles are stored in a prefix. --arch and --profile are used when the prefix is first created.
The run command executes through Wine on a POSIX host; it never loads PE code into the DuckOS process.
)";
}

std::string make_prefix_id(const std::filesystem::path& executable) {
    auto name = executable.stem().string();
    std::string result;
    result.reserve(name.size());
    for (const unsigned char ch : name) {
        if (std::isalnum(ch)) {
            result.push_back(static_cast<char>(std::tolower(ch)));
        } else if (ch == '-' || ch == '_') {
            result.push_back(static_cast<char>(ch));
        } else if (!result.empty() && result.back() != '-') {
            result.push_back('-');
        }
    }
    while (!result.empty() && result.back() == '-') result.pop_back();
    if (result.empty()) result = "windows-app";
    if (result.size() > 64) result.resize(64);
    return result;
}

void print_image(const duckos::compat::PeImageInfo& image) {
    std::cout << "PE image: " << image.file.string() << '\n'
              << "  format: " << duckos::compat::to_string(image.kind) << '\n'
              << "  architecture: " << duckos::compat::to_string(image.architecture) << '\n'
              << "  subsystem: " << duckos::compat::to_string(image.subsystem) << '\n'
              << "  image size: " << image.image_size << " bytes\n"
              << "  entry point RVA: 0x" << std::hex << image.entry_point_rva << std::dec << '\n'
              << "  image type: " << (image.is_dll ? "DLL" : "executable") << '\n'
              << "  relocations: " << (image.has_relocations ? "present" : "absent") << '\n'
              << "  imported modules: " << image.imports.size() << '\n';
    for (const auto& import : image.imports) {
        std::cout << "    - " << import << '\n';
    }
    if (image.architecture == duckos::compat::PeArchitecture::unknown) {
        std::cout << "  warning: unknown CPU architecture; this runner cannot launch it\n";
    }
    if (image.is_dll) {
        std::cout << "  note: DLL files are libraries, not standalone applications\n";
    }
}

std::string option_value(int& index, int argc, char** argv, const std::string& option) {
    if (index + 1 >= argc) {
        throw std::invalid_argument("missing value after " + option);
    }
    return argv[++index];
}

int command_inspect(int argc, char** argv) {
    if (argc != 3) throw std::invalid_argument("inspect expects exactly one file path");
    const auto image = duckos::compat::inspect_pe(argv[2]);
    print_image(image);
    return 0;
}

int command_doctor(int argc, char** argv) {
    auto root = duckos::compat::default_compat_root();
    for (int i = 2; i < argc; ++i) {
        const std::string option = argv[i];
        if (option == "--root") root = option_value(i, argc, argv, option);
        else throw std::invalid_argument("unknown doctor option: " + option);
    }
    duckos::compat::print_diagnostics(root);
    return 0;
}

int command_prefix_create(int argc, char** argv) {
    if (argc < 4) throw std::invalid_argument("prefix create expects an ID");
    const std::string id = argv[3];
    std::string arch = "win64";
    auto profile = duckos::compat::LaunchProfile::utility;
    auto root = duckos::compat::default_compat_root();
    for (int i = 4; i < argc; ++i) {
        const std::string option = argv[i];
        if (option == "--arch") arch = option_value(i, argc, argv, option);
        else if (option == "--profile") profile = duckos::compat::parse_profile(option_value(i, argc, argv, option));
        else if (option == "--root") root = option_value(i, argc, argv, option);
        else throw std::invalid_argument("unknown prefix option: " + option);
    }

    const auto prefix = duckos::compat::create_prefix_layout(root, id, arch, profile);
    std::cout << "Prefix layout created: " << prefix.root << '\n';
    if (duckos::compat::command_available("wineboot")) {
        (void)duckos::compat::initialise_wine_prefix(prefix);
        std::cout << "Wine prefix initialised.\n";
    } else {
        std::cout << "Wine is not installed yet; the prefix will be initialised on the first run.\n";
    }
    return 0;
}

int command_run(int argc, char** argv) {
    if (argc < 3) throw std::invalid_argument("run expects an executable path");
    const std::filesystem::path executable = argv[2];
    auto root = duckos::compat::default_compat_root();
    std::string prefix_id;
    std::string requested_arch = "win64";
    auto requested_profile = duckos::compat::LaunchProfile::utility;
    bool arch_was_set = false;
    bool profile_was_set = false;
    std::vector<std::string> application_arguments;

    int i = 3;
    for (; i < argc; ++i) {
        const std::string option = argv[i];
        if (option == "--") {
            for (++i; i < argc; ++i) application_arguments.emplace_back(argv[i]);
            break;
        }
        if (option == "--prefix") prefix_id = option_value(i, argc, argv, option);
        else if (option == "--root") root = option_value(i, argc, argv, option);
        else if (option == "--arch") {
            requested_arch = option_value(i, argc, argv, option);
            arch_was_set = true;
        } else if (option == "--profile") {
            requested_profile = duckos::compat::parse_profile(option_value(i, argc, argv, option));
            profile_was_set = true;
        } else {
            throw std::invalid_argument("unknown run option: " + option + " (pass game arguments after --)");
        }
    }

    if (requested_arch != "win32" && requested_arch != "win64") {
        throw std::invalid_argument("--arch must be win32 or win64");
    }
    if (!std::filesystem::is_regular_file(executable)) {
        throw std::runtime_error("executable file does not exist: " + executable.string());
    }
    const auto image = duckos::compat::inspect_pe(executable);
    if (image.is_dll) {
        throw std::runtime_error("the selected PE file is a DLL; launch its application or installer instead");
    }
    if (prefix_id.empty()) prefix_id = make_prefix_id(executable);

    const auto config = root / "prefixes" / prefix_id / "prefix.toml";
    duckos::compat::PrefixInfo prefix;
    if (std::filesystem::is_regular_file(config)) {
        prefix = duckos::compat::open_prefix_layout(root, prefix_id);
        if (arch_was_set && requested_arch != prefix.wine_arch) {
            std::cerr << "Notice: existing prefix architecture is " << prefix.wine_arch
                      << "; --arch only applies when creating a prefix.\n";
        }
        if (profile_was_set && requested_profile != prefix.profile) {
            std::cerr << "Notice: existing prefix profile is " << duckos::compat::profile_name(prefix.profile)
                      << "; --profile only applies when creating a prefix.\n";
        }
    } else {
        prefix = duckos::compat::create_prefix_layout(root, prefix_id, requested_arch, requested_profile);
    }

    duckos::compat::RunOptions options;
    options.executable = executable;
    options.compat_root = root;
    options.prefix_id = prefix_id;
    options.arguments = std::move(application_arguments);
    return duckos::compat::run_windows_program(options, image);
}

} // namespace

int main(int argc, char** argv) {
    try {
        if (argc < 2) {
            print_usage();
            return 2;
        }
        const std::string command = argv[1];
        if (command == "help" || command == "--help" || command == "-h") {
            print_usage();
            return 0;
        }
        if (command == "inspect") return command_inspect(argc, argv);
        if (command == "doctor") return command_doctor(argc, argv);
        if (command == "run") return command_run(argc, argv);
        if (command == "prefix") {
            if (argc >= 3 && std::string(argv[2]) == "create") return command_prefix_create(argc, argv);
            throw std::invalid_argument("usage: os-run prefix create <id> [options]");
        }
        throw std::invalid_argument("unknown command: " + command);
    } catch (const duckos::compat::PeFormatError& error) {
        std::cerr << "PE inspection failed: " << error.what() << '\n';
        return 3;
    } catch (const std::exception& error) {
        std::cerr << "os-run: " << error.what() << '\n';
        return 1;
    }
}
