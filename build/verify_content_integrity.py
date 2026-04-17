#!/usr/bin/env python3
"""
verify_content_integrity.py — Verify output HTML preserves upstream text.

Compares the text content of every HTML page in the output against the
corresponding upstream source page. Strips injected overlay elements
(.oc-header, .oc-footer) from the output before comparing, so only
Kuphaldt's original text is checked.

Usage:
    python build/verify_content_integrity.py [--diff] [upstream-dir [output-dir]]

Options:
    --diff      Print a unified diff for each failing page.

Defaults:
    upstream-dir    upstream/html
    output-dir      output/html

Exit codes:
    0   All pages match.
    1   One or more pages have differing text, or output pages are missing.
"""

import argparse
import difflib
import re
import sys
from pathlib import Path

from bs4 import BeautifulSoup

_BADGE_DOMAINS_RE = re.compile(r"ibiblio\.org|validator\.w3\.org|gnu\.org", re.IGNORECASE)

REPO_ROOT = Path(__file__).parent.parent


def extract_tokens(path: Path) -> list[str]:
    """
    Return a list of whitespace-delimited text tokens from an HTML file,
    with .oc-header, .oc-footer, and upstream badge links removed.
    """
    soup = BeautifulSoup(
        path.read_text(encoding="utf-8", errors="replace"), "html.parser"
    )
    for injected in soup.find_all(class_=["oc-header", "oc-footer"]):
        injected.decompose()
    for anchor in soup.find_all("a", href=True):
        if _BADGE_DOMAINS_RE.search(anchor.get("href", "")):
            anchor.decompose()
    return soup.get_text(separator=" ").split()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("upstream_dir", nargs="?", default="upstream/html",
                        type=Path, metavar="upstream-dir")
    parser.add_argument("output_dir", nargs="?", default="output/html",
                        type=Path, metavar="output-dir")
    parser.add_argument("--diff", action="store_true",
                        help="Show a diff for each failing page")
    args = parser.parse_args()

    def resolve(p: Path) -> Path:
        return p if p.is_absolute() else REPO_ROOT / p

    upstream_dir = resolve(args.upstream_dir)
    output_dir = resolve(args.output_dir)

    if not upstream_dir.is_dir():
        print(f"Error: upstream directory not found: {upstream_dir}",
              file=sys.stderr)
        print("Run build/download_source.py first.", file=sys.stderr)
        sys.exit(1)

    if not output_dir.is_dir():
        print(f"Error: output directory not found: {output_dir}",
              file=sys.stderr)
        print("Run overlay/inject_overlay.py first.", file=sys.stderr)
        sys.exit(1)

    passed = failed = missing = 0

    for upstream_file in sorted(upstream_dir.rglob("*.html")):
        rel = upstream_file.relative_to(upstream_dir)
        output_file = output_dir / rel

        if not output_file.exists():
            print(f"MISSING  {rel}")
            missing += 1
            continue

        upstream_tokens = extract_tokens(upstream_file)
        output_tokens = extract_tokens(output_file)

        if upstream_tokens == output_tokens:
            passed += 1
        else:
            print(f"FAIL     {rel}")
            failed += 1
            if args.diff:
                diff_lines = list(difflib.unified_diff(
                    upstream_tokens, output_tokens,
                    fromfile=f"upstream/{rel}",
                    tofile=f"output/{rel}",
                    lineterm="",
                ))
                for line in diff_lines[:40]:
                    print(f"  {line}")
                if len(diff_lines) > 40:
                    print(f"  ... ({len(diff_lines) - 40} more lines)")
                print()

    print()
    print(f"Upstream : {upstream_dir}")
    print(f"Output   : {output_dir}")
    print(f"Results  : {passed} passed, {failed} failed, {missing} missing")

    if failed or missing:
        print("\nCONTENT INTEGRITY CHECK FAILED", file=sys.stderr)
        if not args.diff and failed:
            print("Re-run with --diff to see what changed.", file=sys.stderr)
        sys.exit(1)

    print("\nCONTENT INTEGRITY CHECK PASSED")


if __name__ == "__main__":
    main()
