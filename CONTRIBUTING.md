# Contributing to DuckOS

DuckOS is a Reaper-first operating-system project with a browser-local Mora desktop shell, versioned system contracts and a federated source workspace. Contributions must preserve clear boundaries between browser behavior, reference contracts, packaging tools and native OS work.

## Before opening a pull request

1. State the affected layer: Mora browser shell, Reaper reference contract, Python tooling, source federation or native platform implementation.
2. Include a minimal reproduction, platform details and the exact test/validation command.
3. Keep manifests and schemas versioned; validate paths, sizes, hashes and state transitions.
4. Do not present a catalog item or prototype panel as a shipped native application.
5. Do not describe component bundles or deployment plans as bootable images or physical installations.
6. Preserve safe federation behavior: do not overwrite locally modified submodule work.
7. Keep privileged operations explicit, bounded and evidence-backed; do not add silent disk writes, driver installation or firmware changes.
8. Update the root README, owning contract and documentation index when public behavior changes.

## Initialize and validate the source workspace

~~~sh
git clone --recurse-submodules https://github.com/Ivan-VHS/DuckOS.git
cd DuckOS
python tools/federate_repositories.py sync
~~~

The sync command follows the commits pinned by DuckOS; it is not an upstream update operation.

## Local verification

Use Node.js 18 or newer for the JavaScript contract tests:

~~~sh
npm test
~~~

Run the Python checks:

~~~sh
python -m pip install jsonschema
python -m unittest discover -s tests -v
python tools/validate_app_catalog.py
git diff --check
~~~

For changes to release manifests or deployment planning, also run the relevant schema and tooling tests. Do not test physical-disk operations against a real device; current deployment planning is non-destructive.

## Pull request expectations

Explain compatibility impact, evidence, test coverage, maturity and native/browser boundaries. Include screenshots only when they are genuine captures of the running application. Label SVG architecture drawings as schematics.

## Security and documentation

Do not commit secrets, private user data or machine-local identifiers. Follow [Documentation control](docs/DOCUMENTATION_CONTROL.md), [README Visual Standard](docs/README_VISUAL_STANDARD.md) and the repository's security/capability policies.
