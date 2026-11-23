#pragma once

#include <cstdint>
#include <filesystem>
#include <string>
#include <utility>
#include <vector>

namespace serein {

struct Manifest {
    std::string schemaVersion;
    std::string applicationId;
    std::string project;
    std::string displayName;
    std::string description;
    std::string launchKind;
    std::string entrypoint;
    std::string runtime;
    std::string workingDirectory;
    std::string integrationPolicy;
    std::string trustSource;
    std::string maturityStatus;
    std::string verificationStatus;
    std::vector<std::string> platforms;
    std::vector<std::string> arguments;
    std::vector<std::string> capabilities;
    std::vector<std::pair<std::string, std::string>> platformEntrypoints;
    bool confirmationRequired = false;
    bool shellInterpolation = true;
};

struct RegisteredApp {
    Manifest manifest;
    std::filesystem::path installRoot;
    std::filesystem::path manifestPath;
};

struct ProcessRecord {
    std::uint64_t processId = 0;
    std::uint64_t startToken = 0;
    std::string applicationId;
};

struct LaunchResult {
    std::uint64_t processId = 0;
    std::uint64_t startToken = 0;
};

std::string platformName();
std::filesystem::path defaultRegistryPath();

bool parseManifestText(const std::string& source, Manifest& manifest, std::string& error);
bool parseManifestFile(const std::filesystem::path& path, Manifest& manifest, std::string& error);

bool pathIsWithin(const std::filesystem::path& base, const std::filesystem::path& candidate);
bool resolveAppPath(const std::filesystem::path& installRoot,
                    const std::string& relativePath,
                    std::filesystem::path& resolved,
                    std::string& error);

bool registerApplication(const std::filesystem::path& manifestPath,
                         const std::filesystem::path& installRoot,
                         const std::filesystem::path& registryPath,
                         std::string& error);
bool unregisterApplication(const std::string& applicationId,
                           const std::filesystem::path& registryPath,
                           std::string& error);
std::vector<RegisteredApp> registeredApplications(const std::filesystem::path& registryPath,
                                                   std::vector<std::string>& warnings);
bool findRegisteredApplication(const std::string& applicationId,
                               const std::filesystem::path& registryPath,
                               RegisteredApp& app,
                               std::string& error);

bool launchApplication(const RegisteredApp& app,
                       const std::vector<std::string>& extraArguments,
                       bool foreground,
                       const std::filesystem::path& registryPath,
                       LaunchResult& result,
                       std::string& error);
std::vector<ProcessRecord> activeProcesses(const std::filesystem::path& registryPath,
                                           std::vector<std::string>& warnings);
bool stopProcess(std::uint64_t processId,
                 const std::filesystem::path& registryPath,
                 std::string& error);

std::string quoteForDisplay(const std::string& value);

} // namespace serein