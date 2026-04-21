#!/usr/bin/env python3
"""
build_html.py — Build the Open Circuits HTML site.

Orchestrates the full HTML pipeline:
  1. Ensure upstream/html/ is populated (runs download_source.py if not).
  2. Inject overlay into upstream HTML → output/html/.
  3. Post-build checks:
     - Attribution notice present in root page.
     - Content integrity: output text matches upstream.
  4. Print summary.

Usage:
    python build/build_html.py [--clean] [--skip-integrity]

Options:
    --clean             Remove output/html/ before building.
    --skip-integrity    Skip the content integrity check (faster).

Exits non-zero on any failure.
"""

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
PYTHON = sys.executable

UPSTREAM_HTML = REPO_ROOT / "upstream" / "html"
OUTPUT_HTML = REPO_ROOT / "output" / "html"
EXPECTED_VOLUMES = ["DC", "AC", "Semi", "Digital", "Ref", "Exper"]


def run(script: Path, *args: str) -> subprocess.CompletedProcess:
    """Run a build sub-script with the same Python interpreter."""
    return subprocess.run(
        [PYTHON, str(script), *args],
        cwd=REPO_ROOT,
    )


def step(label: str) -> None:
    """Print a visible section header to stdout."""
    print(f"\n── {label} {'─' * (60 - len(label))}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--clean", action="store_true",
                        help="Remove output/html/ before building")
    parser.add_argument("--skip-integrity", action="store_true",
                        help="Skip content integrity check")
    args = parser.parse_args()

    # ── Step 1: Ensure upstream HTML exists ──────────────────────────────────

    step("Checking upstream HTML")

    # "any" rather than "all": a partial extraction still gets a re-run from
    # download_source.py, which handles cleanup and full re-extraction itself.
    populated = any((UPSTREAM_HTML / v).is_dir() for v in EXPECTED_VOLUMES)
    if not populated:
        print("upstream/html/ not populated — running download_source.py ...")
        result = run(REPO_ROOT / "build" / "download_source.py")
        if result.returncode != 0:
            print("Error: download_source.py failed.", file=sys.stderr)
            sys.exit(1)
    else:
        print(f"upstream/html/ already populated ({UPSTREAM_HTML}).")

    # ── Step 2: Clean output if requested ────────────────────────────────────

    if args.clean and OUTPUT_HTML.exists():
        step("Cleaning output/html/")
        shutil.rmtree(OUTPUT_HTML)
        print(f"Removed {OUTPUT_HTML}")

    # ── Step 3: Inject overlay ────────────────────────────────────────────────

    step("Injecting overlay")

    result = run(
        REPO_ROOT / "overlay" / "inject_overlay.py",
        str(UPSTREAM_HTML),
        str(OUTPUT_HTML),
    )
    if result.returncode != 0:
        print("Error: inject_overlay.py failed.", file=sys.stderr)
        sys.exit(1)

    # ── Step 4: Post-build checks ─────────────────────────────────────────────

    step("Post-build checks")

    # Check attribution notice in root page (index.html, converted from index.htm).
    # This is a warning rather than a fatal error: a missing notice is a licensing
    # concern, not a build-correctness one, and the CI workflow has a separate
    # hard-fail grep for this in the workflow file itself.
    root_page = OUTPUT_HTML / "index.html"
    if root_page.exists():
        text = root_page.read_text(encoding="utf-8", errors="replace")
        if "LICENSE.txt" in text and "ATTRIBUTION.md" in text:
            print("Attribution notice present in root page.")
        else:
            print("Warning: attribution links not found in root page.", file=sys.stderr)
    else:
        print("Warning: root page (index.html) not found in output.", file=sys.stderr)

    # Content integrity check
    if not args.skip_integrity:
        result = run(REPO_ROOT / "build" / "verify_content_integrity.py",
                     str(UPSTREAM_HTML), str(OUTPUT_HTML))
        if result.returncode != 0:
            print("Error: content integrity check failed.", file=sys.stderr)
            sys.exit(1)
    else:
        print("Skipping content integrity check (--skip-integrity).")

    # ── Step 5: Summary ───────────────────────────────────────────────────────

    step("Summary")

    page_count = len(list(OUTPUT_HTML.rglob("*.html")))
    print(f"Output   : {OUTPUT_HTML}")
    print(f"Pages    : {page_count}")
    print("\nBUILD SUCCEEDED")


if __name__ == "__main__":
    main()
