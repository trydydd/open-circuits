#!/usr/bin/env python3
"""
download_source.py — Fetch Kuphaldt's pre-built HTML bundle from ibiblio.

Usage:
    python build/download_source.py [--force]

Options:
    --force     Re-download even if upstream/html/ is already populated.

On success:
    - upstream/html/ contains the extracted volume directories
    - upstream/UPSTREAM-VERSION.txt is updated with snapshot date and URL

Exits non-zero on download or extraction failure.
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
    if total_size <= 0:
        return
    downloaded = min(block_num * block_size, total_size)
    pct = downloaded * 100 / total_size
    bar = "#" * int(pct // 2)
    print(f"\r  [{bar:<50}] {pct:5.1f}%", end="", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true",
                        help="Re-download even if already populated")
    args = parser.parse_args()

    html_dir = REPO_ROOT / "upstream" / "html"
    version_file = REPO_ROOT / "upstream" / "UPSTREAM-VERSION.txt"
    tarball = REPO_ROOT / "upstream" / "liechtml.tar.gz"

    # ── Idempotency check ────────────────────────────────────────────────────

    if not args.force and any((html_dir / v).is_dir() for v in EXPECTED_VOLUMES):
        print("upstream/html/ already populated. Skipping download.")
        print("Use --force to re-download.")
        return

    # ── Download ─────────────────────────────────────────────────────────────

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

    # ── Extract ───────────────────────────────────────────────────────────────

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

    snapshot_date = date.today().isoformat()
    version_file.write_text(
        "# Upstream Source Version\n"
        "# Written by build/download_source.py — do not edit manually.\n\n"
        f"SOURCE_URL={SOURCE_URL}\n"
        f"SNAPSHOT_DATE={snapshot_date}\n"
        "TARBALL=liechtml.tar.gz\n",
        encoding="utf-8",
    )
    print(f"Updated {version_file} (snapshot date: {snapshot_date})")

    # ── Clean up tarball ──────────────────────────────────────────────────────

    tarball.unlink()
    print("Removed tarball.")

    print(f"\nDone. upstream/html/ contents: "
          f"{sorted(p.name for p in html_dir.iterdir())}")


if __name__ == "__main__":
    main()
