"""DuckOS desktop runtime contracts."""

from .audit import AuditLog, SerialLogWriter
from .bench import BenchController, BenchError, load_bench_profile, validate_bench_profile
from .catalog import CatalogError, load_system_catalog, system_app_ids
from .launcher import LauncherError, LauncherRegistry
from .packages import PackageTrustError, PackageTrustStore, SignatureEvidence, sha256_file
from .updates import ABUpdateError, ABUpdateManager

__all__ = [
    "ABUpdateError",
    "ABUpdateManager",
    "AuditLog",
    "BenchController",
    "BenchError",
    "CatalogError",
    "LauncherError",
    "LauncherRegistry",
    "PackageTrustError",
    "PackageTrustStore",
    "SerialLogWriter",
    "SignatureEvidence",
    "load_bench_profile",
    "load_system_catalog",
    "sha256_file",
    "system_app_ids",
    "validate_bench_profile",
]
