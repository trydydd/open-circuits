#!/usr/bin/env python3
"""
download_source.py — Extract Kuphaldt's pre-built HTML bundle.

Primary path: extracts from the vendored upstream/liechtml.tar.gz (Git LFS).
Fallback path: downloads the tarball from ibiblio if the LFS file is absent
               (e.g. a shallow clone without LFS, or a first-time local setup).

Usage:
    python build/download_source.py [--force] [--fetch]

Options:
    --force     Re-extract even if upstream/html/ is already populated.
    --fetch     Force a fresh download from ibiblio, replacing the local tarball.
                Use this when you want to update the vendored tarball.

On success:
    - upstream/html/ contains the extracted volume directories
    - upstream/UPSTREAM-VERSION.txt is updated
"""

import argparse
import shutil
import sys
import tarfile
import urllib.request
from datetime import date
from pathlib import Path

SOURCE_URL = "https://www.ibiblio.org/kuphaldt/electricCircuits/liechtml.tar.gz"
EXPECTED_VOLUMES = ["DC", "AC", "Semi", "Digital", "Ref", "Exper"]

REPO_ROOT = Path(__file__).parent.parent


def progress_hook(block_num: int, block_size: int, total_size: int) -> None:
    """urllib.request.urlretrieve callback that prints a progress bar to stdout."""
    if total_size <= 0:
        return
    downloaded = min(block_num * block_size, total_size)
    pct = downloaded * 100 / total_size
    bar = "#" * int(pct // 2)
    print(f"\r  [{bar:<50}] {pct:5.1f}%", end="", flush=True)


def download_tarball(tarball: Path) -> None:
    """Download the upstream tarball from ibiblio to disk. Exits non-zero on failure."""
    print(f"Downloading {SOURCE_URL} ...")
    tarball.parent.mkdir(parents=True, exist_ok=True)
    try:
        urllib.request.urlretrieve(SOURCE_URL, tarball, reporthook=progress_hook)
        print()  # newline after progress bar
    except Exception as exc:
        print(f"\nDownload failed: {exc}", file=sys.stderr)
        tarball.unlink(missing_ok=True)
        sys.exit(1)
    print(f"Download complete: {tarball}")


def extract_tarball(tarball: Path, html_dir: Path) -> None:
    """Extract the tarball into html_dir, replacing any existing contents. Exits non-zero on failure."""
    print(f"Extracting to {html_dir} ...")
    if html_dir.exists():
        shutil.rmtree(html_dir)
    html_dir.mkdir(parents=True)
    try:
        with tarfile.open(tarball) as tf:
            tf.extractall(html_dir)
    except Exception as exc:
        print(f"Extraction failed: {exc}", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true",
                        help="Re-extract even if upstream/html/ is already populated")
    parser.add_argument("--fetch", action="store_true",
                        help="Download a fresh copy from ibiblio (updates vendored tarball)")
    args = parser.parse_args()

    html_dir = REPO_ROOT / "upstream" / "html"
    version_file = REPO_ROOT / "upstream" / "UPSTREAM-VERSION.txt"
    tarball = REPO_ROOT / "upstream" / "liechtml.tar.gz"

    # ── Idempotency check ────────────────────────────────────────────────────

    if not args.force and not args.fetch and any((html_dir / v).is_dir() for v in EXPECTED_VOLUMES):
        print("upstream/html/ already populated. Skipping extraction.")
        print("Use --force to re-extract.")
        return

    # ── Obtain tarball ───────────────────────────────────────────────────────

    downloaded_fresh = False

    if args.fetch or not tarball.exists():
        if not args.fetch:
            print("Vendored tarball not found — downloading from ibiblio (fallback).")
            print("To use Git LFS: git lfs pull")
        download_tarball(tarball)
        downloaded_fresh = True
    else:
        print(f"Using vendored tarball: {tarball}")

    # ── Extract ───────────────────────────────────────────────────────────────

    extract_tarball(tarball, html_dir)

    # Clean up only if we downloaded a fresh copy (not an LFS-managed file)
    if downloaded_fresh and not args.fetch:
        tarball.unlink()
        print("Removed downloaded tarball (not managed by LFS).")

    # ── Validate ──────────────────────────────────────────────────────────────

    missing = [v for v in EXPECTED_VOLUMES if not (html_dir / v).is_dir()]
    if missing:
        print(f"Warning: expected volume directories not found: {missing}",
              file=sys.stderr)
        print(f"Contents of {html_dir}: {list(html_dir.iterdir())}",
              file=sys.stderr)
        print("The tarball structure may have changed. Proceeding anyway.",
              file=sys.stderr)

    # ── Write version file ────────────────────────────────────────────────────

    source = "ibiblio (downloaded)" if downloaded_fresh else "Git LFS"
    version_file.write_text(
        "# Upstream Source Version\n"
        "# Written by build/download_source.py — do not edit manually.\n\n"
        f"SOURCE_URL={SOURCE_URL}\n"
        f"EXTRACTION_DATE={date.today().isoformat()}\n"
        f"SOURCE={source}\n"
        "TARBALL=liechtml.tar.gz\n",
        encoding="utf-8",
    )
    print(f"Updated {version_file}")

    print(f"\nDone. upstream/html/ contents: "
          f"{sorted(p.name for p in html_dir.iterdir())}")


if __name__ == "__main__":
    main()
