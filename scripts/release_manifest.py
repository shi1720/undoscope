#!/usr/bin/env python3
"""Generate or check SHA-256 hashes for the versioned artifact (excluding itself)."""
import argparse
import hashlib
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "release/SHA256SUMS"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    names = subprocess.check_output(
        ["git", "ls-files", "-z"], cwd=ROOT
    ).decode().split("\0")
    paths = sorted(n for n in names if n and n != "release/SHA256SUMS")
    content = "".join(
        f"{hashlib.sha256((ROOT / name).read_bytes()).hexdigest()}  {name}\n"
        for name in paths
    )
    if args.check:
        if not MANIFEST.exists() or MANIFEST.read_text() != content:
            raise SystemExit("Release manifest does not match versioned files.")
        print(f"Verified {len(paths)} versioned artifact files.")
    else:
        MANIFEST.parent.mkdir(exist_ok=True)
        MANIFEST.write_text(content)
        print(f"Recorded {len(paths)} versioned artifact files.")


if __name__ == "__main__":
    main()
