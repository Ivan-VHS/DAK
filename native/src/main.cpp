#include "serein/serein.hpp"

#include <algorithm>
#include <charconv>
#include <cstdio>
#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <string>
#include <vector>

#ifdef _WIN32
#include <io.h>
#else
#include <unistd.h>
#endif

namespace {

bool inputIsInteractive() {
#ifdef _WIN32
    return _isatty(_fileno(stdin)) != 0;
#else
    return ::isatty(STDIN_FILENO) != 0;
#endif
}

bool askConfirmation(const std::string& question, bool explicitlyConfirmed, bool allowPrompt) {
    if (explicitlyConfirmed) return true;
    if (!allowPrompt || !inputIsInteractive()) {
        std::cerr << "Confirmation is required. Run this command from a terminal or add --confirm.\n";
        return false;
    }

    std::cout << question << " [y/N] ";
    std::string answer;
    if (!std::getline(std::cin, answer)) return false;
    return answer == "y" || answer == "Y" || answer == "yes" || answer == "YES";
}

void printHelp() {
    std::cout
        << "Serein — native application manager for DuckOS\n\n"
        << "Usage:\n"
        << "  serein                         Open the Serein command console\n"
        << "  serein apps                    List registered applications\n"
        << "  serein register MANIFEST --root DIR [--confirm]\n"
        << "  serein unregister APP_ID [--confirm]\n"
        << "  serein inspect APP_ID\n"
        << "  serein run APP_ID [--foreground] [--confirm] [-- APP_ARGS...]\n"
        << "  serein ps                      List processes launched by Serein\n"
        << "  serein stop PID [--confirm]    Stop a tracked process\n"
        << "  serein help                    Show this help\n"
        << "  serein version                 Show version and platform\n\n"
        << "Examples:\n"
        << "  serein register integrations/mora/manifest.json --root .\n"
        << "  serein apps\n"
        << "  serein run ivan-vhs.reaper-studio\n"
        << "  serein ps\n"
        << "  serein shell\n\n"
        << "Serein does not interpret shell commands, variables, pipes or redirects.\n"
        << "Application arguments are passed as an argument vector, never through a shell.\n"
        << "All registered applications require explicit confirmation before launch.\n";
}

bool parsePositiveInteger(const std::string& text, std::uint64_t& value) {
    if (text.empty()) return false;
    const auto result = std::from_chars(text.data(), text.data() + text.size(), value);
    return result.ec == std::errc{} && result.ptr == text.data() + text.size() && value > 0;
}

void printWarnings(const std::vector<std::string>& warnings) {
    for (const auto& warning : warnings) std::cerr << "Warning: " << warning << '\n';
}

bool printApps(const std::filesystem::path& registry) {
    std::vector<std::string> warnings;
    const auto applications = serein::registeredApplications(registry, warnings);
    printWarnings(warnings);
    if (applications.empty()) {
        std::cout << "No applications registered.\n"
                  << "Use: serein register MANIFEST --root INSTALL_DIRECTORY\n";
        return true;
    }

    std::cout << "Registered applications\n";
    for (const auto& app : applications) {
        std::cout << "  " << app.manifest.applicationId << "\n"
                  << "    " << app.manifest.displayName << " — " << app.manifest.project << "\n"
                  << "    " << app.manifest.maturityStatus << " · " << app.manifest.integrationPolicy << "\n";
    }
    return true;
}

bool printInspection(const std::string& applicationId,
                     const std::filesystem::path& registry) {
    serein::RegisteredApp app;
    std::string error;
    if (!serein::findRegisteredApplication(applicationId, registry, app, error)) {
        std::cerr << "Cannot inspect application: " << error << '\n';
        return false;
    }

    std::cout << app.manifest.displayName << " (" << app.manifest.applicationId << ")\n"
              << "  Project:       " << app.manifest.project << '\n'
              << "  Description:   " << app.manifest.description << '\n'
              << "  Install root:  " << app.installRoot.string() << '\n'
              << "  Entry point:   " << app.manifest.entrypoint << '\n'
              << "  Runtime:       " << (app.manifest.runtime.empty() ? "native executable" : app.manifest.runtime) << '\n'
              << "  Platforms:     ";
    for (std::size_t i = 0; i < app.manifest.platforms.size(); ++i) {
        if (i) std::cout << ", ";
        std::cout << app.manifest.platforms[i];
    }
    std::cout << "\n"
              << "  Maturity:      " << app.manifest.maturityStatus << '\n'
              << "  Verification:  " << app.manifest.verificationStatus << '\n'
              << "  Policy:        " << app.manifest.integrationPolicy << '\n'
              << "  Trust source:  " << app.manifest.trustSource << '\n'
              << "  Confirmation:  required\n"
              << "  Shell:         disabled\n";
    return true;
}

bool printProcesses(const std::filesystem::path& registry) {
    std::vector<std::string> warnings;
    const auto processes = serein::activeProcesses(registry, warnings);
    printWarnings(warnings);
    if (processes.empty()) {
        std::cout << "No active Serein-managed processes.\n";
        return true;
    }

    std::cout << "PID        APPLICATION\n";
    for (const auto& process : processes) {
        std::cout << process.processId << "   " << process.applicationId << '\n';
    }
    return true;
}

bool dispatch(const std::vector<std::string>& tokens,
              const std::filesystem::path& registry,
              bool allowPrompt,
              bool& shouldExit) {
    if (tokens.empty()) return true;
    const std::string& command = tokens[0];

    if (command == "help" || command == "?") {
        printHelp();
        return true;
    }
    if (command == "version") {
        std::cout << "Serein 0.2.0 · DuckOS · " << serein::platformName() << '\n';
        return true;
    }
    if (command == "exit" || command == "quit") {
        shouldExit = true;
        return true;
    }
    if (command == "clear") {
        std::cout << "\x1b[2J\x1b[H";
        return true;
    }
    if (command == "apps" || command == "list") {
        if (tokens.size() != 1) {
            std::cerr << "Usage: apps\n";
            return false;
        }
        return printApps(registry);
    }
    if (command == "ps") {
        if (tokens.size() != 1) {
            std::cerr << "Usage: ps\n";
            return false;
        }
        return printProcesses(registry);
    }
    if (command == "inspect") {
        if (tokens.size() != 2) {
            std::cerr << "Usage: inspect APP_ID\n";
            return false;
        }
        return printInspection(tokens[1], registry);
    }
    if (command == "register") {
        if (tokens.size() < 4) {
            std::cerr << "Usage: register MANIFEST --root INSTALL_DIRECTORY [--confirm]\n";
            return false;
        }
        bool hasRoot = false;
        bool confirmed = false;
        std::string root;
        for (std::size_t i = 2; i < tokens.size(); ++i) {
            if (tokens[i] == "--root" && i + 1 < tokens.size()) {
                root = tokens[++i];
                hasRoot = true;
            } else if (tokens[i] == "--confirm") {
                confirmed = true;
            } else {
                std::cerr << "Unknown register option: " << tokens[i] << '\n';
                return false;
            }
        }
        if (!hasRoot) {
            std::cerr << "register requires --root INSTALL_DIRECTORY\n";
            return false;
        }
        if (!askConfirmation("Register this manifest as a trusted local application?", confirmed, allowPrompt)) return false;
        std::string error;
        if (!serein::registerApplication(std::filesystem::u8path(tokens[1]),
                                         std::filesystem::u8path(root), registry, error)) {
            std::cerr << "Registration failed: " << error << '\n';
            return false;
        }
        std::cout << "Application registered. Inspect it with: serein inspect <app-id>\n";
        return true;
    }
    if (command == "unregister") {
        if (tokens.size() < 2 || tokens.size() > 3) {
            std::cerr << "Usage: unregister APP_ID [--confirm]\n";
            return false;
        }
        const bool confirmed = tokens.size() == 3 && tokens[2] == "--confirm";
        if (tokens.size() == 3 && !confirmed) {
            std::cerr << "Unknown unregister option: " << tokens[2] << '\n';
            return false;
        }
        if (!askConfirmation("Remove this application registration? Its installed files will not be deleted.", confirmed, allowPrompt)) return false;
        std::string error;
        if (!serein::unregisterApplication(tokens[1], registry, error)) {
            std::cerr << "Unregister failed: " << error << '\n';
            return false;
        }
        std::cout << "Application registration removed.\n";
        return true;
    }
    if (command == "run" || command == "launch") {
        if (tokens.size() < 2) {
            std::cerr << "Usage: run APP_ID [--foreground] [--confirm] [-- APP_ARGS...]\n";
            return false;
        }
        bool foreground = false;
        bool confirmed = false;
        bool argumentsStarted = false;
        std::vector<std::string> extraArguments;
        for (std::size_t i = 2; i < tokens.size(); ++i) {
            if (argumentsStarted) {
                extraArguments.push_back(tokens[i]);
            } else if (tokens[i] == "--") {
                argumentsStarted = true;
            } else if (tokens[i] == "--foreground") {
                foreground = true;
            } else if (tokens[i] == "--confirm") {
                confirmed = true;
            } else {
                std::cerr << "Unknown run option: " << tokens[i] << ". Place application arguments after --.\n";
                return false;
            }
        }

        serein::RegisteredApp app;
        std::string error;
        if (!serein::findRegisteredApplication(tokens[1], registry, app, error)) {
            std::cerr << "Application is not registered: " << error << '\n';
            return false;
        }
        std::cout << "Application: " << app.manifest.displayName << '\n'
                  << "Project: " << app.manifest.project << '\n'
                  << "Install root: " << app.installRoot.string() << '\n';
        if (!askConfirmation("Launch this application?", confirmed, allowPrompt)) return false;

        serein::LaunchResult result;
        if (!serein::launchApplication(app, extraArguments, foreground, registry, result, error)) {
            std::cerr << "Launch failed: " << error << '\n';
            return false;
        }
        if (foreground) {
            std::cout << "Foreground process finished (PID " << result.processId << ").\n";
        } else {
            std::cout << "Launched and tracked process " << result.processId << ". Use 'ps' or 'stop " << result.processId << "'.\n";
        }
        return true;
    }
    if (command == "stop") {
        if (tokens.size() < 2 || tokens.size() > 3) {
            std::cerr << "Usage: stop PID [--confirm]\n";
            return false;
        }
        std::uint64_t processId = 0;
        if (!parsePositiveInteger(tokens[1], processId)) {
            std::cerr << "PID must be a positive integer.\n";
            return false;
        }
        const bool confirmed = tokens.size() == 3 && tokens[2] == "--confirm";
        if (tokens.size() == 3 && !confirmed) {
            std::cerr << "Unknown stop option: " << tokens[2] << '\n';
            return false;
        }
        if (!askConfirmation("Stop Serein-managed process " + std::to_string(processId) + "?", confirmed, allowPrompt)) return false;
        std::string error;
        if (!serein::stopProcess(processId, registry, error)) {
            std::cerr << "Stop failed: " << error << '\n';
            return false;
        }
        std::cout << "Stop signal sent to process " << processId << ".\n";
        return true;
    }

    std::cerr << "Unknown Serein command: " << command << ". Type 'help' for available commands.\n";
    return false;
}

bool tokenize(const std::string& line, std::vector<std::string>& tokens, std::string& error) {
    tokens.clear();
    std::string current;
    char quote = '\0';
    bool tokenStarted = false;
    bool escaping = false;

    for (const char c : line) {
        if (escaping) {
            if (c == quote || c == '\\') current.push_back(c);
            else { current.push_back('\\'); current.push_back(c); }
            escaping = false;
            tokenStarted = true;
            continue;
        }
        if (quote != '\0') {
            if (c == quote) quote = '\0';
            else if (c == '\\' && quote == '"') escaping = true;
            else current.push_back(c);
            tokenStarted = true;
            continue;
        }
        if (c == '"' || c == '\'') {
            quote = c;
            tokenStarted = true;
        } else if (c == ' ' || c == '\t') {
            if (tokenStarted) {
                tokens.push_back(std::move(current));
                current.clear();
                tokenStarted = false;
            }
        } else {
            current.push_back(c);
            tokenStarted = true;
        }
    }
    if (escaping || quote != '\0') {
        error = "Unterminated quoted argument or escape.";
        return false;
    }
    if (tokenStarted) tokens.push_back(std::move(current));
    return true;
}

int runConsole(const std::filesystem::path& registry) {
    std::cout << "Serein — DuckOS application console\n"
              << "Type 'help' for commands. This is not a general-purpose shell.\n";
    bool shouldExit = false;
    std::string line;
    while (!shouldExit) {
        std::cout << "serein > " << std::flush;
        if (!std::getline(std::cin, line)) break;
        std::vector<std::string> tokens;
        std::string error;
        if (!tokenize(line, tokens, error)) {
            std::cerr << "Input error: " << error << '\n';
            continue;
        }
        (void)dispatch(tokens, registry, true, shouldExit);
    }
    return 0;
}

} // namespace

int main(int argc, char** argv) {
    std::filesystem::path registry = serein::defaultRegistryPath();
    int index = 1;
    if (argc > 2 && std::string(argv[index]) == "--registry") {
        registry = std::filesystem::u8path(argv[index + 1]);
        index += 2;
    }

    if (index >= argc) return runConsole(registry);

    std::vector<std::string> tokens;
    for (int i = index; i < argc; ++i) tokens.emplace_back(argv[i]);
    bool shouldExit = false;
    const bool success = dispatch(tokens, registry, inputIsInteractive(), shouldExit);
    return success ? 0 : 1;
}