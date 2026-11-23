#include "serein/serein.hpp"

#include <filesystem>
#include <fstream>
#include <iostream>
#include <string>

namespace fs = std::filesystem;

namespace {

int failures = 0;

void check(bool condition, const std::string& message) {
    if (!condition) {
        ++failures;
        std::cerr << "FAIL: " << message << '\n';
    } else {
        std::cout << "PASS: " << message << '\n';
    }
}

const std::string validManifest = R"JSON({
  "$schema": "https://github.com/Ivan-VHS/DuckOS/blob/main/mora/app-manifest.schema.json",
  "schema_version": "1.0.0",
  "application_id": "test.serein-app",
  "project": "Ivan-VHS/SereinFixture",
  "display_name": "Serein Fixture",
  "description": "A local fixture used by the native process-manager tests.",
  "launch": {
    "kind": "local_process",
    "platforms": ["windows", "linux", "macos"],
    "entrypoint": "bin/fixture.bin",
    "platform_entrypoints": {
      "windows": "bin/fixture.exe"
    },
    "runtime": "",
    "arguments": ["--safe-mode"],
    "working_directory": "."
  },
  "policy": {
    "integration_policy": "opt_in",
    "confirmation_required": true,
    "shell_interpolation": false,
    "trust_source": "operator_installed_project"
  },
  "maturity": {
    "maturity_status": "specified",
    "verification_status": "not_run"
  },
  "capabilities": ["test-process", "manifest-validation"]
})JSON";

void testManifestParser() {
    serein::Manifest manifest;
    std::string error;
    check(serein::parseManifestText(validManifest, manifest, error), "valid v1 manifest is accepted");
    check(manifest.applicationId == "test.serein-app", "application ID is retained");
    check(manifest.platformEntrypoints.size() == 1, "platform-specific entry point is read");
    check(manifest.confirmationRequired && !manifest.shellInterpolation,
          "the manifest requires confirmation and disables shell interpolation");

    auto invalid = validManifest;
    const auto marker = invalid.find("\"shell_interpolation\": false");
    invalid.replace(marker, std::string("\"shell_interpolation\": false").size(),
                    "\"shell_interpolation\": true");
    check(!serein::parseManifestText(invalid, manifest, error),
          "manifests that enable shell interpolation are rejected");

    invalid = validManifest;
    invalid.insert(invalid.find("\"capabilities\""), "\"extra\": \"not allowed\",\n  ");
    check(!serein::parseManifestText(invalid, manifest, error),
          "unknown manifest properties are rejected");

    invalid = validManifest;
    invalid.insert(invalid.find("\"schema_version\""), "\"schema_version\": \"1.0.0\",\n  ");
    check(!serein::parseManifestText(invalid, manifest, error),
          "duplicate JSON keys are rejected");

    invalid = validManifest;
    const auto pathMarker = invalid.find("\"entrypoint\": \"bin/fixture.bin\"");
    invalid.replace(pathMarker, std::string("\"entrypoint\": \"bin/fixture.bin\"").size(),
                    "\"entrypoint\": \"../outside.bin\"");
    check(serein::parseManifestText(invalid, manifest, error),
          "path strings are parsed before filesystem resolution");
}

void testPathConfinement(const fs::path& root) {
    std::string error;
    fs::path resolved;
    check(serein::resolveAppPath(root, "bin/fixture.bin", resolved, error),
          "a regular file inside the registered root resolves");
    check(!serein::resolveAppPath(root, "../outside.bin", resolved, error),
          "parent-directory traversal is rejected");
    check(!serein::resolveAppPath(root, "missing.bin", resolved, error),
          "missing paths are rejected");

    const fs::path sibling = root.parent_path() / (root.filename().string() + "-outside");
    check(!serein::pathIsWithin(root, sibling),
          "path-prefix siblings are not mistaken for children");

#ifndef _WIN32
    std::error_code ec;
    const fs::path link = root / "bin" / "outside-link";
    fs::create_symlink(sibling / "secret.txt", link, ec);
    if (!ec) {
        check(!serein::resolveAppPath(root, "bin/outside-link", resolved, error),
              "a symlink that escapes the installation root is rejected");
    }
#endif
}

void testRegistration(const fs::path& root, const fs::path& registry) {
    const fs::path manifestFile = root / "manifest.json";
    {
        std::ofstream output(manifestFile, std::ios::binary);
        output << validManifest;
    }

    std::string error;
    check(serein::registerApplication(manifestFile, root, registry, error),
          "an explicit local installation can be registered");
    check(!serein::registerApplication(manifestFile, root, registry, error),
          "duplicate application registration is refused");

    serein::RegisteredApp app;
    check(serein::findRegisteredApplication("test.serein-app", registry, app, error),
          "a registered app can be loaded again");
    check(app.manifest.applicationId == "test.serein-app" && app.installRoot == fs::canonical(root),
          "the registration keeps its validated identity and canonical root");

    std::vector<std::string> warnings;
    const auto applications = serein::registeredApplications(registry, warnings);
    check(applications.size() == 1, "the registry lists exactly one valid app");

    check(serein::unregisterApplication("test.serein-app", registry, error),
          "an app can be unregistered without deleting its installation");
    check(!serein::findRegisteredApplication("test.serein-app", registry, app, error),
          "an unregistered app is no longer launchable");
    check(fs::exists(root / "bin" / "fixture.bin"),
          "unregistering leaves application files untouched");
}

} // namespace

int main() {
    testManifestParser();

    const fs::path base = fs::temp_directory_path() / "duckos-serein-contract-tests";
    const fs::path root = base / "project";
    const fs::path registry = base / "registry";

    std::error_code ec;
    fs::remove_all(base, ec);
    fs::create_directories(root / "bin", ec);
    fs::create_directories(base / "project-outside", ec);
    {
        std::ofstream fixture(root / "bin" / "fixture.bin", std::ios::binary);
        fixture << "fixture";
        std::ofstream secret(base / "project-outside" / "secret.txt", std::ios::binary);
        secret << "outside";
    }

    testPathConfinement(root);
    testRegistration(root, registry);

    fs::remove_all(base, ec);
    if (failures != 0) {
        std::cerr << failures << " Serein test(s) failed.\n";
        return 1;
    }
    std::cout << "All Serein contract tests passed.\n";
    return 0;
}