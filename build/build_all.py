#!/usr/bin/env python3
"""
build_all.py — Full Open Circuits build pipeline.

Runs the complete build sequence:
  1. download_source.py   — fetch upstream HTML from ibiblio
  2. build_html.py        — inject overlay, validate output
  3. build_zim.py         — build Kiwix ZIM file (skipped if script not found)
  4. Create release tarball: output/open-circuits-<version>.tar.gz

Usage:
    python build/build_all.py [--clean] [--skip-integrity]

Options:
    --clean             Remove output/html/ before building.
    --skip-integrity    Skip the content integrity check.

Exits non-zero if any required step fails.
"""

import argparse
import subprocess
import sys
import tarfile
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
PYTHON = sys.executable

OUTPUT_DIR = REPO_ROOT / "output"
OUTPUT_HTML = OUTPUT_DIR / "html"


def run(script: Path, *args: str) -> int:
    """Run a build sub-script with the same Python interpreter and return its exit code."""
    result = subprocess.run([PYTHON, str(script), *args], cwd=REPO_ROOT)
    return result.returncode


def git_version() -> str:
    """Return the current git tag (e.g. 'v1.2.0') for release tarball naming.

    Falls back to 'dev' for untagged commits, shallow clones, or environments
    where git is unavailable — keeping build_all.py runnable outside a full repo.
    """
    result = subprocess.run(
        ["git", "describe", "--tags", "--always"],
        capture_output=True, text=True, cwd=REPO_ROOT,
    )
    return result.stdout.strip() if result.returncode == 0 else "dev"


def step(label: str) -> None:
    """Print a visible section header to stdout."""
    print(f"\n{'═' * 64}")
    print(f"  {label}")
    print(f"{'═' * 64}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--clean", action="store_true",
                        help="Remove output/html/ before building")
    parser.add_argument("--skip-integrity", action="store_true",
                        help="Skip content integrity check")
    args = parser.parse_args()

    extra = []
    if args.clean:
        extra.append("--clean")
    if args.skip_integrity:
        extra.append("--skip-integrity")

    # ── Step 1: Download ──────────────────────────────────────────────────────

    step("Step 1/4 — Download upstream HTML")
    rc = run(REPO_ROOT / "build" / "download_source.py")
    if rc != 0:
        print("Error: download_source.py failed.", file=sys.stderr)
        sys.exit(1)

    # ── Step 2: Build HTML ────────────────────────────────────────────────────

    step("Step 2/4 — Build HTML site")
    rc = run(REPO_ROOT / "build" / "build_html.py", *extra)
    if rc != 0:
        print("Error: build_html.py failed.", file=sys.stderr)
        sys.exit(1)

    # ── Step 3: Build ZIM (optional) ─────────────────────────────────────────

    step("Step 3/4 — Build ZIM package")
    zim_script = REPO_ROOT / "build" / "build_zim.py"
    if zim_script.exists():
        rc = run(zim_script)
        if rc != 0:
            print("Error: build_zim.py failed.", file=sys.stderr)
            sys.exit(1)
    else:
        print("build_zim.py not found — skipping ZIM build.")

    # ── Step 4: Create release tarball ───────────────────────────────────────

    step("Step 4/4 — Create release tarball")

    if not OUTPUT_HTML.is_dir():
        print(f"Error: {OUTPUT_HTML} not found — cannot create tarball.",
              file=sys.stderr)
        sys.exit(1)

    version = git_version()
    tarball_path = OUTPUT_DIR / f"open-circuits-{version}.tar.gz"

    print(f"Version  : {version}")
    print(f"Archiving: {OUTPUT_HTML} → {tarball_path}")

    with tarfile.open(tarball_path, "w:gz") as tf:
        tf.add(OUTPUT_HTML, arcname="open-circuits")

    size_mb = tarball_path.stat().st_size / (1024 * 1024)
    print(f"Created  : {tarball_path.name} ({size_mb:.1f} MB)")

    # ── Done ──────────────────────────────────────────────────────────────────

    print(f"\n{'═' * 64}")
    print("  BUILD ALL SUCCEEDED")
    print(f"{'═' * 64}")
    print(f"  HTML  : {OUTPUT_HTML}")
    print(f"  TAR   : {tarball_path}")


if __name__ == "__main__":
    main()
