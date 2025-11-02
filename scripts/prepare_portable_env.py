#!/usr/bin/env python3
"""
Prepare a self-contained Python runtime for the portable Electron build.

This script uses ``conda-pack`` to copy an existing conda environment into
``portable/python`` so that the packaged app can ship with its own interpreter
and dependencies.

Usage:
    python scripts/prepare_portable_env.py --env legalai
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PORTABLE_DIR = ROOT / "portable" / "python"


def run(*cmd: str) -> None:
    """Run a command and raise if it fails."""
    result = subprocess.run(cmd, check=False)
    if result.returncode != 0:
        raise RuntimeError(f"Command failed ({result.returncode}): {' '.join(cmd)}")


def ensure_conda_pack() -> None:
    """Ensure ``conda-pack`` is available."""
    try:
        subprocess.run(["conda-pack", "--help"], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        raise RuntimeError(
            "conda-pack is required. Install with `conda install -c conda-forge conda-pack`."
        ) from exc


def pack_environment(env_name: str, ignore_missing: bool) -> Path:
    """Pack the conda environment into a temporary zip and return its path."""
    ensure_conda_pack()

    tmp_dir = Path(tempfile.mkdtemp(prefix="portable_env_"))
    archive_path = tmp_dir / "python_env.zip"

    print(f"[prepare-portable] Packing conda env '{env_name}'...")
    cmd = ["conda-pack", "-n", env_name, "-o", str(archive_path)]
    if ignore_missing:
        cmd.append("--ignore-missing-files")
    run(*cmd)
    return archive_path


def unpack_archive(archive: Path) -> None:
    """Extract the packed archive into the portable directory."""
    if PORTABLE_DIR.exists():
        print(f"[prepare-portable] Removing existing portable runtime: {PORTABLE_DIR}")
        shutil.rmtree(PORTABLE_DIR)

    PORTABLE_DIR.parent.mkdir(parents=True, exist_ok=True)

    print(f"[prepare-portable] Extracting runtime to {PORTABLE_DIR}...")
    run("python", "-m", "zipfile", "-e", str(archive), str(PORTABLE_DIR))

    # Clean up conda activation scripts which are not needed
    cleanup_dirs = ["conda-meta", "pkgs"]
    for dirname in cleanup_dirs:
        path = PORTABLE_DIR / dirname
        if path.exists():
            shutil.rmtree(path)

    # Ensure python.exe is at top-level Scripts or root depending on pack layout
    scripts_dir = PORTABLE_DIR / "Scripts"
    if scripts_dir.exists():
        python_exe = scripts_dir / "python.exe"
        if python_exe.exists():
            target = PORTABLE_DIR / "python.exe"
            print(f"[prepare-portable] Copying python.exe to {target}")
            shutil.copy2(python_exe, target)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--env",
        default="legalai",
        help="Name of the conda environment to pack (default: legalai)",
    )
    parser.add_argument(
        "--ignore-missing",
        action="store_true",
        help="Ignore missing conda-managed files (useful if pip overwrote metadata)",
    )
    args = parser.parse_args()

    archive = pack_environment(args.env, args.ignore_missing)
    try:
        unpack_archive(archive)
    finally:
        if archive.exists():
            archive.unlink()
        if archive.parent.exists():
            shutil.rmtree(archive.parent, ignore_errors=True)

    print("[prepare-portable] Portable Python runtime ready.")


if __name__ == "__main__":
    main()
