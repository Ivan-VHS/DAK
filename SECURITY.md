# DuckOS security policy

DuckOS security changes are reviewed as system-boundary changes. Report suspected vulnerabilities through the repository's GitHub Security tab or a private vulnerability-reporting channel provided by GitHub. Do not publish exploit details, secrets, private keys, personal data or live attack material in public issues.

## Current protection boundaries

- Mora is a browser desktop shell; its UI preferences do not enforce kernel or process permissions.
- Sentinel stores deny-by-default shell preferences; native permission enforcement still requires a privileged broker and OS support.
- File inspection is local and read-only by default. A digest alone does not establish signer identity or safety.
- The BAV module currently implements bounded, local, descriptive context classification only. It is not a complete antivirus engine.
- Context labels in `security/defense-context.v1.tsv` are not malware signatures. They must never independently block, delete or quarantine a file.
- Native sandboxing, process monitoring, signature trust, real-time protection and recovery remain separate implementation work until supported by code and tests.

## Security references

- [Defensive security doctrine and BAV context taxonomy](docs/DEFENSIVE_SECURITY_DOCTRINE.md)
- [BAV context module scope and self-test](bav/README.md)
- [Mora integration and permission boundaries](docs/MORA_INTEGRATION.md)

## Review requirements

Security-sensitive changes require a documented threat model, bounded input validation, least privilege, explicit trust boundaries, tests for negative cases and an auditable rollback path. Do not claim a capability is implemented or verified based solely on a UI control, specification or placeholder.
