#!/usr/bin/env python3
"""
build_zim.py — Build a Kiwix ZIM file from the Open Circuits HTML output.

Requires zimwriterfs to be installed:
    Ubuntu/Debian : sudo apt install zimwriterfs
    macOS         : brew install kiwix-tools
    Manual        : https://github.com/openzim/zim-tools

Usage:
    python build/build_zim.py [--output PATH]

Options:
    --output PATH   Path for the output .zim file
                    (default: output/open-circuits.zim)

Exits non-zero if zimwriterfs is unavailable or the build fails.
"""

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent

OUTPUT_HTML = REPO_ROOT / "output" / "html"
ZIM_META    = REPO_ROOT / "zim-metadata"
DEFAULT_ZIM = REPO_ROOT / "output" / "open-circuits.zim"


def read_meta(key: str) -> str:
    """Extract a value from metadata.yaml (simple key: value parser)."""
    meta_file = ZIM_META / "metadata.yaml"
    for line in meta_file.read_text(encoding="utf-8").splitlines():
        if line.startswith(f"{key}:"):
            return line.split(":", 1)[1].strip()
    return ""


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_ZIM,
                        metavar="PATH", help="Output .zim file path")
    args = parser.parse_args()

    zim_out: Path = args.output

    # ── Check zimwriterfs ─────────────────────────────────────────────────────

    if not shutil.which("zimwriterfs"):
        print("zimwriterfs not found — skipping ZIM build.")
        print("Install it with one of:")
        print("  Ubuntu/Debian : sudo apt install zimwriterfs")
        print("  macOS         : brew install kiwix-tools")
        print("  Manual        : https://github.com/openzim/zim-tools")
        sys.exit(0)

    # ── Check prerequisites ───────────────────────────────────────────────────

    if not OUTPUT_HTML.is_dir():
        print(f"Error: {OUTPUT_HTML} not found.", file=sys.stderr)
        print("Run build/build_html.py first.", file=sys.stderr)
        sys.exit(1)

    root_page = OUTPUT_HTML / "index.html"
    if not root_page.exists():
        print(f"Error: root page not found: {root_page}", file=sys.stderr)
        sys.exit(1)

    # ── Build ─────────────────────────────────────────────────────────────────

    zim_out.parent.mkdir(parents=True, exist_ok=True)
    if zim_out.exists():
        zim_out.unlink()

    title       = read_meta("Title")
    description = read_meta("Description")
    language    = read_meta("Language")
    creator     = read_meta("Creator")
    publisher   = read_meta("Publisher")
    tags        = read_meta("Tags")

    cmd = [
        "zimwriterfs",
        f"--welcome=index.html",
        f"--illustration={ZIM_META / 'illustration.png'}",
        f"--favicon={ZIM_META / 'favicon.png'}",
        f"--language={language}",
        f"--title={title}",
        f"--description={description}",
        f"--creator={creator}",
        f"--publisher={publisher}",
        f"--tags={tags}",
        f"--name=open-circuits",
        str(OUTPUT_HTML),
        str(zim_out),
    ]

    print(f"Running zimwriterfs ...")
    print(f"  Source : {OUTPUT_HTML}")
    print(f"  Output : {zim_out}")

    result = subprocess.run(cmd, cwd=REPO_ROOT)
    if result.returncode != 0:
        print("Error: zimwriterfs failed.", file=sys.stderr)
        sys.exit(1)

    # ── Validate ──────────────────────────────────────────────────────────────

    if not zim_out.exists() or zim_out.stat().st_size == 0:
        print(f"Error: ZIM file missing or empty: {zim_out}", file=sys.stderr)
        sys.exit(1)

    size_mb = zim_out.stat().st_size / (1024 * 1024)
    print(f"ZIM created: {zim_out} ({size_mb:.1f} MB)")
    print("Done.")


if __name__ == "__main__":
    main()
