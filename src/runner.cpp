#include "duckos/compat/runner.hpp"

#include <cerrno>
#include <cstdlib>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>
#include <system_error>
#include <vector>

#if defined(__unix__) || defined(__APPLE__)
#include <sys/types.h>
#include <sys/wait.h>
#include <unistd.h>
#endif

namespace duckos::compat {
namespace {

#if defined(__unix__) || defined(__APPLE__)

int wait_for_child(pid_t child) {
    int status = 0;
    while (::waitpid(child, &status, 0) < 0) {
        if (errno == EINTR) continue;
        throw std::runtime_error("waitpid failed: " + std::string(std::strerror(errno)));
    }
    if (WIFEXITED(status)) return WEXITSTATUS(status);
    if (WIFSIGNALED(status)) return 128 + WTERMSIG(status);
    return 1;
}

int run_captured(const std::vector<std::string>& arguments,
                 const std::vector<std::pair<std::string, std::string>>& environment,
                 const std::filesystem::path& log_file) {
    if (arguments.empty()) {
        throw std::invalid_argument("cannot execute an empty command");
    }

    std::filesystem::create_directories(log_file.parent_path());
    std::ofstream log(log_file, std::ios::binary | std::ios::app);
    if (!log) {
        throw std::runtime_error("cannot open run log: " + log_file.string());
    }

    int output_pipe[2];
    if (::pipe(output_pipe) != 0) {
        throw std::runtime_error("pipe failed: " + std::string(std::strerror(errno)));
    }

    const pid_t child = ::fork();
    if (child < 0) {
        const auto message = std::string(std::strerror(errno));
        ::close(output_pipe[0]);
        ::close(output_pipe[1]);
        throw std::runtime_error("fork failed: " + message);
    }

    if (child == 0) {
        ::close(output_pipe[0]);
        if (::dup2(output_pipe[1], STDOUT_FILENO) < 0 || ::dup2(output_pipe[1], STDERR_FILENO) < 0) {
            _exit(126);
        }
        ::close(output_pipe[1]);
        for (const auto& [key, value] : environment) {
            if (::setenv(key.c_str(), value.c_str(), 1) != 0) _exit(126);
        }

        std::vector<char*> argv;
        argv.reserve(arguments.size() + 1);
        for (const auto& argument : arguments) {
            argv.push_back(const_cast<char*>(argument.c_str()));
        }
        argv.push_back(nullptr);
        ::execvp(argv.front(), argv.data());
        const auto error = errno;
        const std::string message = "duckos-os-run: cannot start '" + arguments.front() + "': " + std::strerror(error) + "\n";
        (void)::write(STDERR_FILENO, message.data(), message.size());
        _exit(error == ENOENT ? 127 : 126);
    }

    ::close(output_pipe[1]);
    char buffer[4096];
    for (;;) {
        const auto count = ::read(output_pipe[0], buffer, sizeof(buffer));
        if (count == 0) break;
        if (count < 0) {
            if (errno == EINTR) continue;
            ::close(output_pipe[0]);
            (void)wait_for_child(child);
            throw std::runtime_error("reading child output failed: " + std::string(std::strerror(errno)));
        }
        log.write(buffer, count);
        log.flush();
        std::streamsize written = 0;
        while (written < count) {
            const auto amount = ::write(STDOUT_FILENO, buffer + written, static_cast<std::size_t>(count - written));
            if (amount < 0) {
                if (errno == EINTR) continue;
                break;
            }
            written += amount;
        }
    }
    ::close(output_pipe[0]);
    const int exit_code = wait_for_child(child);
    log << "\n[duckos] process_exit_code = " << exit_code << "\n";
    log.flush();
    return exit_code;
}

#endif

std::string debug_level_for(LaunchProfile profile) {
    switch (profile) {
    case LaunchProfile::utility: return "-all";
    case LaunchProfile::retro: return "err+all";
    case LaunchProfile::modern: return "err+all";
    }
    return "-all";
}

void append_session_header(const PrefixInfo& prefix,
                           const std::filesystem::path& executable,
                           const PeImageInfo& image) {
    const auto log_file = prefix.logs / "session.log";
    std::ofstream log(log_file, std::ios::binary | std::ios::app);
    if (!log) {
        throw std::runtime_error("cannot write session log: " + log_file.string());
    }
    log << "\n--- DuckOS Windows compatibility session ---\n"
        << "executable = " << executable.string() << "\n"
        << "architecture = " << to_string(image.architecture) << "\n"
        << "format = " << to_string(image.kind) << "\n"
        << "subsystem = " << to_string(image.subsystem) << "\n"
        << "profile = " << profile_name(prefix.profile) << "\n"
        << "prefix = " << prefix.wine_prefix.string() << "\n"
        << "backend = wine\n";
}

} // namespace

bool command_available(const std::string& command) {
#if defined(__unix__) || defined(__APPLE__)
    if (command.find('/') != std::string::npos) {
        return ::access(command.c_str(), X_OK) == 0;
    }
    const char* path = std::getenv("PATH");
    if (path == nullptr) return false;
    std::string paths(path);
    std::size_t start = 0;
    while (start <= paths.size()) {
        const auto end = paths.find(':', start);
        const auto directory = paths.substr(start, end == std::string::npos ? std::string::npos : end - start);
        const auto candidate = std::filesystem::path(directory.empty() ? "." : directory) / command;
        if (::access(candidate.c_str(), X_OK) == 0) return true;
        if (end == std::string::npos) break;
        start = end + 1;
    }
#endif
    return false;
}

int initialise_wine_prefix(const PrefixInfo& prefix) {
#if defined(__unix__) || defined(__APPLE__)
    if (!command_available("wineboot")) {
        throw std::runtime_error("wineboot was not found; install Wine before creating a runnable prefix");
    }
    std::vector<std::pair<std::string, std::string>> environment{
        {"WINEPREFIX", std::filesystem::absolute(prefix.wine_prefix).string()},
        {"WINEARCH", prefix.wine_arch},
        {"WINEDEBUG", "-all"}
    };
    const int status = run_captured({"wineboot", "-u"}, environment, prefix.logs / "wineboot.log");
    if (status != 0) {
        throw std::runtime_error("wineboot failed with exit code " + std::to_string(status) + "; see " + (prefix.logs / "wineboot.log").string());
    }
    return status;
#else
    (void)prefix;
    throw std::runtime_error("the Wine process backend currently requires a POSIX host");
#endif
}

int run_windows_program(const RunOptions& options, const PeImageInfo& image) {
#if defined(__unix__) || defined(__APPLE__)
    if (!command_available("wine")) {
        throw std::runtime_error("Wine was not found. Install Wine or configure a Proton-backed runtime before launching Windows applications.");
    }

    auto prefix = open_prefix_layout(options.compat_root, options.prefix_id);
    if (image.architecture == PeArchitecture::unknown || image.architecture == PeArchitecture::arm64) {
        throw std::runtime_error("this Wine backend supports x86 and x86_64 PE files only; detected " + std::string(to_string(image.architecture)));
    }
    if (prefix.wine_arch == "win32" && image.architecture == PeArchitecture::x86_64) {
        throw std::runtime_error("a 64-bit executable cannot run in a win32 prefix; create a win64 prefix");
    }

    const auto wine_prefix = std::filesystem::absolute(prefix.wine_prefix);
    if (!std::filesystem::is_regular_file(wine_prefix / "system.reg")) {
        std::cout << "Initialising Wine prefix '" << prefix.id << "'...\n";
        (void)initialise_wine_prefix(prefix);
    }

    const auto executable = std::filesystem::absolute(options.executable);
    append_session_header(prefix, executable, image);

    std::vector<std::pair<std::string, std::string>> environment{
        {"WINEPREFIX", wine_prefix.string()},
        {"WINEDEBUG", debug_level_for(prefix.profile)},
        {"DUCKOS_PREFIX_ID", prefix.id},
        {"DUCKOS_PROFILE", profile_name(prefix.profile)}
    };
    if (!std::getenv("WINEESYNC")) {
        environment.emplace_back("WINEESYNC", prefix.profile == LaunchProfile::modern ? "1" : "0");
    }

    std::vector<std::string> command{"wine", executable.string()};
    command.insert(command.end(), options.arguments.begin(), options.arguments.end());
    std::cout << "Launching with Wine. Prefix: " << prefix.id
              << ", profile: " << profile_name(prefix.profile)
              << ", PE: " << to_string(image.architecture) << "\n";
    std::cout << "Log: " << (prefix.logs / "session.log").string() << "\n";
    return run_captured(command, environment, prefix.logs / "session.log");
#else
    (void)options;
    (void)image;
    throw std::runtime_error("the Wine process backend currently requires a POSIX host");
#endif
}

void print_diagnostics(const std::filesystem::path& compat_root) {
    const auto check = [](const char* name) {
        std::cout << "  " << name << ": " << (command_available(name) ? "available" : "not found") << '\n';
    };
    std::cout << "DuckOS Windows compatibility diagnostics\n"
              << "  data root: " << compat_root.string() << '\n';
    check("wine");
    check("wineboot");
    check("wineserver");
    check("winetricks");
    check("vulkaninfo");
    check("glxinfo");
    std::cout << "\nNotes:\n"
              << "  - DXVK and VKD3D-Proton are not bundled; install/configure them per Wine or Proton prefix.\n"
              << "  - Vulkan availability does not prove DirectX translation is installed or working.\n"
              << "  - Prefix isolation is not a kernel sandbox; launched programs retain the current user's host permissions.\n"
              << "  - Kernel-mode anti-cheat drivers are not supported by this userspace Wine runner.\n";
}

} // namespace duckos::compat
