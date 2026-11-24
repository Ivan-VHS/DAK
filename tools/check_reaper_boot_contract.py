from __future__ import annotations

import argparse
import os
from pathlib import Path
import subprocess
import sys
import tempfile

EXPECTED = "0\n0\n-2\n-3\n-4\n-5\n-6\n-6\n-7\n"
MAX_OUTPUT_CHARS = 1_000_000


class ContractCheckError(RuntimeError):
    pass


def run(command: list[str], *, cwd: Path, timeout: int) -> subprocess.CompletedProcess[str]:
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            shell=False,
            check=False,
        )
    except subprocess.TimeoutExpired as error:
        raise ContractCheckError(f"command exceeded the {timeout}-second limit: {command[0]}") from error
    except OSError as error:
        raise ContractCheckError(f"cannot start {command[0]}: {error}") from error

    if len(result.stdout) > MAX_OUTPUT_CHARS or len(result.stderr) > MAX_OUTPUT_CHARS:
        raise ContractCheckError(f"command output exceeded {MAX_OUTPUT_CHARS} characters")
    if result.returncode != 0:
        details = (result.stderr or result.stdout).strip()
        raise ContractCheckError(
            f"command failed with exit code {result.returncode}: {details[:4000]}"
        )
    return result


def verify(reaper_root: Path, c_harness: Path) -> dict[str, object]:
    root = reaper_root.expanduser().resolve(strict=True)
    harness = c_harness.expanduser().resolve(strict=True)
    if not root.is_dir() or not (root / "reaper" / "__main__.py").is_file():
        raise ContractCheckError("Reaper root is not a valid source checkout")
    if not harness.is_file():
        raise ContractCheckError("C conformance harness does not exist")

    relative_source = Path("targets") / "duckos" / "boot_contract_v1.rpr"
    source = root / relative_source
    if source.is_symlink() or not source.is_file():
        raise ContractCheckError("pinned Reaper checkout does not contain the DuckOS boot target")
    source = source.resolve(strict=True)
    if root not in source.parents:
        raise ContractCheckError("DuckOS target source escapes the Reaper checkout")

    python = sys.executable
    run(
        [python, "-m", "reaper", "--check", "--syntax-only", str(source)],
        cwd=root,
        timeout=30,
    )
    reference = run(
        [python, "-m", "reaper", str(source)],
        cwd=root,
        timeout=30,
    )
    if reference.stdout != EXPECTED:
        raise ContractCheckError(
            "Reaper reference runtime output differs from the expected fixture matrix"
        )

    with tempfile.TemporaryDirectory(prefix="duckos-reaper-contract-") as folder:
        output = Path(folder) / ("boot-contract.exe" if os.name == "nt" else "boot-contract")
        run(
            [python, "-m", "reaper", str(source), "--native", str(output)],
            cwd=root,
            timeout=150,
        )
        native = run([str(output)], cwd=root, timeout=30)
        c_result = run([str(harness)], cwd=root, timeout=30)

    if native.stdout != reference.stdout:
        raise ContractCheckError("Reaper native AOT output differs from its reference runtime")
    if c_result.stdout != reference.stdout:
        raise ContractCheckError("Reaper output differs from the DuckOS C boot contract")
    return {
        "schema": "duckos.reaper-boot-contract-check.v1",
        "valid": True,
        "target": str(relative_source).replace("\\", "/"),
        "fixtures": len(EXPECTED.splitlines()),
        "reference_runtime": "pass",
        "native_aot": "pass",
        "duckos_c_contract": "pass",
        "status_stream": EXPECTED.splitlines(),
        "execution_performed": False,
        "hardware_accessed": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Compare Reaper's DuckOS boot-info v1 model with the DuckOS C contract."
    )
    parser.add_argument("--reaper-root", type=Path, required=True)
    parser.add_argument("--c-harness", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        report = verify(args.reaper_root, args.c_harness)
    except (ContractCheckError, OSError, ValueError) as error:
        print(f"duckos-reaper-contract: {error}", file=sys.stderr)
        return 2
    import json
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
