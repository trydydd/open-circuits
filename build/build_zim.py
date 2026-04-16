#!/usr/bin/env python3
"""
build_zim.py — Build a Kiwix ZIM file from the Open Circuits HTML output.

Requires zimwriterfs to be installed, or pass --use-docker to run via the
official ghcr.io/openzim/zimwriterfs container (Docker must be available).

    Ubuntu/Debian : sudo apt install zimwriterfs
    macOS         : brew install kiwix-tools
    Docker        : python build/build_zim.py --use-docker
    Manual        : https://github.com/openzim/zim-tools

Usage:
    python build/build_zim.py [--output PATH] [--use-docker]

Options:
    --output PATH   Path for the output .zim file
                    (default: output/open-circuits.zim)
    --use-docker    Run zimwriterfs via the official Docker container instead
                    of a locally-installed binary.

Exits non-zero if zimwriterfs/docker is unavailable or the build fails.
Exits 0 (with a skip message) if neither zimwriterfs nor --use-docker is
available — so build_all.py can call this without failing local dev builds.
"""

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).parent.parent

OUTPUT_HTML = REPO_ROOT / "output" / "html"
ZIM_META    = REPO_ROOT / "zim-metadata"
DEFAULT_ZIM = REPO_ROOT / "output" / "open-circuits.zim"

ZIMWRITERFS_IMAGE = "ghcr.io/openzim/zimwriterfs:latest"


def load_meta() -> dict:
    """Load and normalise ZIM metadata from metadata.yaml."""
    meta_file = ZIM_META / "metadata.yaml"
    raw = yaml.safe_load(meta_file.read_text(encoding="utf-8"))

    desc = raw.get("Description", "")
    if isinstance(desc, str):
        desc = " ".join(desc.split())  # collapse block-scalar newlines

    return {
        "title":       str(raw.get("Title",     "")),
        "description": desc,
        "language":    str(raw.get("Language",  "")),
        "creator":     str(raw.get("Creator",   "")),
        "publisher":   str(raw.get("Publisher", "")),
        "tags":        str(raw.get("Tags",      "")),
        "name":        str(raw.get("Name",      "open-circuits")),
    }


def zimwriterfs_cmd(meta: dict, zim_out: Path,
                    html_dir: str, meta_dir: str) -> list[str]:
    """Return the zimwriterfs argument list (paths already resolved for caller)."""
    return [
        "zimwriterfs",
        "--welcome=index.html",
        f"--illustration={meta_dir}/illustration.png",
        f"--favicon={meta_dir}/favicon.png",
        f"--language={meta['language']}",
        f"--title={meta['title']}",
        f"--description={meta['description']}",
        f"--creator={meta['creator']}",
        f"--publisher={meta['publisher']}",
        f"--tags={meta['tags']}",
        f"--name={meta['name']}",
        html_dir,
        str(zim_out),
    ]


def build_local(meta: dict, zim_out: Path) -> None:
    """Build ZIM using a locally-installed zimwriterfs binary."""
    cmd = zimwriterfs_cmd(meta, zim_out,
                          str(OUTPUT_HTML), str(ZIM_META))
    print("Running zimwriterfs ...")
    print(f"  Source : {OUTPUT_HTML}")
    print(f"  Output : {zim_out}")
    result = subprocess.run(cmd, cwd=REPO_ROOT)
    if result.returncode != 0:
        print("Error: zimwriterfs failed.", file=sys.stderr)
        sys.exit(1)


def build_docker(meta: dict, zim_out: Path) -> None:
    """Build ZIM via the official ghcr.io/openzim/zimwriterfs Docker container."""
    if not shutil.which("docker"):
        print("Error: docker not found — cannot use --use-docker.", file=sys.stderr)
        sys.exit(1)

    out_dir = zim_out.parent.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    html_mount = "/html"
    meta_mount = "/meta"
    out_mount  = "/out"

    zim_args = zimwriterfs_cmd(meta, Path(f"{out_mount}/{zim_out.name}"),
                                html_mount, meta_mount)

    cmd = [
        "docker", "run", "--rm",
        "-v", f"{OUTPUT_HTML.resolve()}:{html_mount}:ro",
        "-v", f"{ZIM_META.resolve()}:{meta_mount}:ro",
        "-v", f"{out_dir}:{out_mount}",
        ZIMWRITERFS_IMAGE,
        *zim_args,
    ]

    print(f"Running zimwriterfs via Docker ({ZIMWRITERFS_IMAGE}) ...")
    print(f"  Source : {OUTPUT_HTML}")
    print(f"  Output : {zim_out}")
    result = subprocess.run(cmd, cwd=REPO_ROOT)
    if result.returncode != 0:
        print("Error: zimwriterfs Docker container failed.", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_ZIM,
                        metavar="PATH", help="Output .zim file path")
    parser.add_argument("--use-docker", action="store_true",
                        help="Run zimwriterfs via the official Docker container")
    args = parser.parse_args()

    zim_out: Path = args.output

    # ── Check prerequisites ───────────────────────────────────────────────────

    if not OUTPUT_HTML.is_dir():
        print(f"Error: {OUTPUT_HTML} not found.", file=sys.stderr)
        print("Run build/build_html.py first.", file=sys.stderr)
        sys.exit(1)

    if not (OUTPUT_HTML / "index.html").exists():
        print(f"Error: root page not found: {OUTPUT_HTML / 'index.html'}",
              file=sys.stderr)
        sys.exit(1)

    # ── Select build method ───────────────────────────────────────────────────

    if args.use_docker:
        meta = load_meta()
        zim_out.parent.mkdir(parents=True, exist_ok=True)
        if zim_out.exists():
            zim_out.unlink()
        build_docker(meta, zim_out)
    elif shutil.which("zimwriterfs"):
        meta = load_meta()
        zim_out.parent.mkdir(parents=True, exist_ok=True)
        if zim_out.exists():
            zim_out.unlink()
        build_local(meta, zim_out)
    else:
        print("zimwriterfs not found — skipping ZIM build.")
        print("Install it with one of:")
        print("  Ubuntu/Debian : sudo apt install zimwriterfs")
        print("  macOS         : brew install kiwix-tools")
        print("  Docker        : python build/build_zim.py --use-docker")
        print("  Manual        : https://github.com/openzim/zim-tools")
        sys.exit(0)

    # ── Validate ──────────────────────────────────────────────────────────────

    if not zim_out.exists() or zim_out.stat().st_size == 0:
        print(f"Error: ZIM file missing or empty: {zim_out}", file=sys.stderr)
        sys.exit(1)

    size_mb = zim_out.stat().st_size / (1024 * 1024)
    print(f"ZIM created: {zim_out} ({size_mb:.1f} MB)")
    print("Done.")


if __name__ == "__main__":
    main()
