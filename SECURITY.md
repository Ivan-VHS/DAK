# DuckOS Security Policy

DuckOS is an experimental operating-system project. Its boot image, policy layer, and Mora host application have separate trust boundaries. See [Implementation Status](docs/IMPLEMENTATION_STATUS.md) and the [Defensive Security Doctrine](docs/DEFENSIVE_SECURITY_DOCTRINE.md) before treating any capability as available.

## Reporting a vulnerability

Do not publish exploit details, credentials, private device identifiers, or a working exploit in a public issue or pull request.

Use the repository's **Security → Report a vulnerability** flow when private vulnerability reporting is available. If that option is not enabled, contact the repository maintainer through GitHub and request a private reporting channel. This policy does not promise a response-time SLA.

Include, where safe, the affected commit/component/platform, impact and preconditions, a minimal non-destructive reproduction, expected and observed behavior, and redacted logs. Do not attach real credentials, private keys, customer data, or unredacted device identifiers.

## Scope and current limitations

Security-relevant surfaces include the freestanding boot boundary, firmware handoff validation, Reaper policy contracts, versioned service/package schemas, release artifacts, and the local Mora host application.

The current project does not claim a production process model, kernel-enforced capabilities, a native service supervisor, a driver loader, a cryptographic firmware trust chain, or a native desktop compositor. Reference policies and read-only inspectors do not enforce kernel isolation.

## Safe handling rules

- Treat source, package manifests, firmware images, archives, and plugin metadata as untrusted input.
- Bound parsers by size, depth, count, and time; reject malformed encodings and path traversal.
- Do not execute or load inspected artifacts during validation.
- Do not add device writes, firmware flashing, driver installation, process injection, or privileged host mutation without a separately reviewed scope and explicit authorization.
- Keep telemetry local by default; do not silently upload source, device identifiers, file paths, or reports.
- Keep context classification separate from malware verdicts; a topic match is not evidence of malicious behavior.

Security fixes should include regression tests and identify the trust boundary they change.
