# Serein native component

Serein is DuckOS's C++20 application registry, manifest validator and process launcher.

See the [Serein documentation](../docs/SEREIN.md) for its command reference, manifest contract, path policy, process model and build instructions.

The command-line executable is **serein**. The implementation uses native process APIs directly and never routes manifest data through a command shell.