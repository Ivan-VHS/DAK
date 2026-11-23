# DuckOS Hardware Agent

Python 3 standard library only. Start with a read-only report:

\`\`\`powershell
python agent/duckos_hardware_agent.py snapshot --output hardware-snapshot.json
\`\`\`

Windows driver operations are separate:

\`\`\`powershell
python agent/duckos_hardware_agent.py export-drivers --output D:\\DuckOSDriverBackup
python agent/duckos_hardware_agent.py scan-driver-updates --output driver-offers.json
python agent/duckos_hardware_agent.py install-driver-update --update-id <GUID> --backup-dir D:\\DuckOSDriverBackup
\`\`\`

The export folder must be empty and the path absolute. Run elevated for a full Driver Store export. Installation is never unattended: the agent rechecks the exact Windows Update ID, asks for a confirmation phrase, exports the existing Driver Store and creates a Windows System Restore checkpoint before installing one offer. A failed prerequisite aborts the operation.

Linux snapshot collection reads sysfs/procfs/DMI/EFI where available. It does not invoke a package manager, load/unload modules or write firmware. macOS currently receives only a platform-level report.

Reports are local JSON files. Do not upload them publicly without reviewing them; hardware identifiers and machine details can be sensitive.
