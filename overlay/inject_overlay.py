#!/usr/bin/env python3
"""
inject_overlay.py — Inject CSS link, header, and footer into upstream HTML.

Usage:
    python overlay/inject_overlay.py <input-dir> <output-dir>

What it does:
    - Copies every .html file from input-dir into output-dir, preserving
      subdirectory structure.
    - Inserts <link rel="stylesheet"> into <head>.
    - Injects header.html content after the opening <body> tag.
    - Injects footer.html content before the closing </body> tag.
    - Resolves {{PLACEHOLDER}} tokens so paths are correct at any depth.
    - Copies overlay/css/ and overlay/js/ into output-dir.
    - Validates that no external <link> or <script> resource URLs appear
      outside the injected .oc-footer; exits non-zero if found.

Exits non-zero on any error.
"""

import argparse
import re
import shutil
import sys
from pathlib import Path

from bs4 import BeautifulSoup

OVERLAY_DIR = Path(__file__).parent
REPO_ROOT = OVERLAY_DIR.parent

TEMPLATES_DIR = OVERLAY_DIR / "templates"
CSS_SRC = OVERLAY_DIR / "css"
JS_SRC = OVERLAY_DIR / "js"
FONTS_SRC = OVERLAY_DIR / "fonts"

# Tokens resolved in header/footer templates
TEMPLATE_KEYS = [
    "INDEX_PATH",
    "VOL_DC", "VOL_AC", "VOL_SEMI", "VOL_DIGITAL", "VOL_REF", "VOL_EXPER",
    "LICENSE_PATH", "ATTRIBUTION_PATH",
    "JS_PATH",
]

# Upstream pages include hosting/validation badge links from these domains
_BADGE_DOMAINS_RE = re.compile(r"ibiblio\.org|validator\.w3\.org|gnu\.org", re.IGNORECASE)


def resolve_paths(depth: int) -> dict[str, str]:
    """Return template substitution values for a file at `depth` levels deep."""
    p = "../" * depth
    return {
        "INDEX_PATH":       f"{p}index.html",
        "VOL_DC":           f"{p}DC/DC_1.html",
        "VOL_AC":           f"{p}AC/AC_1.html",
        "VOL_SEMI":         f"{p}Semi/SEMI_1.html",
        "VOL_DIGITAL":      f"{p}Digital/DIGI_1.html",
        "VOL_REF":          f"{p}Ref/REF_1.html",
        "VOL_EXPER":        f"{p}Exper/EXP_1.html",
        "LICENSE_PATH":     f"{p}LICENSE.txt",
        "ATTRIBUTION_PATH": f"{p}ATTRIBUTION.md",
        "JS_PATH":          f"{p}js/",
    }


def _strip_badge_links(content: str) -> str:
    """Remove upstream hosting/validation badge <a> links from page content."""
    soup = BeautifulSoup(content, "html.parser")
    badges = [a for a in soup.find_all("a", href=True)
              if _BADGE_DOMAINS_RE.search(a.get("href", ""))]
    if not badges:
        return content
    for badge in badges:
        badge.decompose()
    return str(soup)


def render_template(tmpl_path: Path, subs: dict[str, str]) -> str:
    text = tmpl_path.read_text(encoding="utf-8")
    for key, val in subs.items():
        text = text.replace("{{" + key + "}}", val)
    return text.strip()


def inject_file(src: Path, dst: Path, depth: int) -> None:
    """Read src, inject overlay elements, write to dst."""
    subs = resolve_paths(depth)
    css_href = f"{'../' * depth}css/open-circuits.css"
    js_href  = f"{'../' * depth}js/navigation.js"
    css_link  = f'<link rel="stylesheet" href="{css_href}">'
    js_tag    = f'<script src="{js_href}" defer></script>'
    viewport  = '<meta name="viewport" content="width=device-width, initial-scale=1">'
    header_html = render_template(TEMPLATES_DIR / "header.html", subs)
    footer_html = render_template(TEMPLATES_DIR / "footer.html", subs)

    content = src.read_text(encoding="utf-8", errors="replace")
    content = _strip_badge_links(content)

    # Insert viewport meta, CSS link, and JS script before </head> (case-insensitive)
    content, n = re.subn(
        r"(</head>)", f"{viewport}\n{css_link}\n{js_tag}\n\\1", content, count=1, flags=re.IGNORECASE
    )
    if n == 0:
        # No </head> — prepend to file as fallback
        content = f"{viewport}\n{css_link}\n{js_tag}\n{content}"

    # Strip inline style/bgcolor from <body> tag so our CSS theme isn't overridden
    content = re.sub(
        r"(<body)([^>]*)(>)",
        lambda m: m.group(1) + re.sub(r'\s*(?:style|bgcolor)\s*=\s*(?:"[^"]*"|\'[^\']*\'|\S+)', '', m.group(2), flags=re.IGNORECASE) + m.group(3),
        content, count=1, flags=re.IGNORECASE
    )

    # Inject header after opening <body ...> tag
    content, n = re.subn(
        r"(<body[^>]*>)", f"\\1\n{header_html}", content, count=1, flags=re.IGNORECASE
    )
    if n == 0:
        content = f"{header_html}\n{content}"

    # Inject footer before </body>
    content, n = re.subn(
        r"(</body>)", f"{footer_html}\n\\1", content, count=1, flags=re.IGNORECASE
    )
    if n == 0:
        content = f"{content}\n{footer_html}"

    # Rewrite local .htm hrefs/srcs to .html — upstream uses .htm but we rename all files
    content = re.sub(
        r'(href|src)="(?!https?://)([^"]*?)\.htm"',
        lambda m: f'{m.group(1)}="{m.group(2)}.html"',
        content,
        flags=re.IGNORECASE,
    )

    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(content, encoding="utf-8")


def validate_no_external_resources(output_dir: Path) -> list[str]:
    """
    Return a list of violation strings for any <link href> or <script src>
    pointing to an external URL, outside the .oc-footer region.
    """
    violations = []
    for html_file in sorted(output_dir.rglob("*.html")):
        soup = BeautifulSoup(
            html_file.read_text(encoding="utf-8", errors="replace"), "html.parser"
        )
        # Exclude the injected footer from the check
        for footer in soup.find_all(class_="oc-footer"):
            footer.decompose()

        for tag in soup.find_all(["link", "script"]):
            url = tag.get("href") or tag.get("src") or ""
            if re.match(r"https?://", url, re.IGNORECASE):
                violations.append(f"{html_file.relative_to(output_dir)}: {tag}")

    return violations


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_dir", type=Path,
                        help="Directory containing upstream HTML tree")
    parser.add_argument("output_dir", type=Path,
                        help="Directory to write modified HTML tree into")
    args = parser.parse_args()

    input_dir: Path = args.input_dir
    output_dir: Path = args.output_dir

    if not input_dir.is_dir():
        print(f"Error: input directory not found: {input_dir}", file=sys.stderr)
        sys.exit(1)

    for tmpl in ["header.html", "footer.html"]:
        if not (TEMPLATES_DIR / tmpl).exists():
            print(f"Error: template not found: {TEMPLATES_DIR / tmpl}",
                  file=sys.stderr)
            sys.exit(1)

    output_dir.mkdir(parents=True, exist_ok=True)

    # ── Process HTML files ────────────────────────────────────────────────────

    html_files = sorted(
        f for ext in ("*.html", "*.htm") for f in input_dir.rglob(ext)
    )
    for src in html_files:
        rel = src.relative_to(input_dir)
        # Normalise .htm → .html in output
        if rel.suffix.lower() == ".htm":
            rel = rel.with_suffix(".html")
        dst = output_dir / rel
        depth = len(rel.parts) - 1
        inject_file(src, dst, depth)

    print(f"Processed {len(html_files)} HTML page(s) → {output_dir}")

    # ── Copy upstream non-HTML assets (images, etc.) ─────────────────────────

    html_suffixes = {".html", ".htm"}
    asset_files = [
        f for f in input_dir.rglob("*")
        if f.is_file() and f.suffix.lower() not in html_suffixes
    ]
    for src in asset_files:
        dst = output_dir / src.relative_to(input_dir)
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)

    print(f"Copied {len(asset_files)} asset file(s) → {output_dir}")

    # ── Copy overlay static assets ────────────────────────────────────────────

    if CSS_SRC.is_dir():
        dst_css = output_dir / "css"
        shutil.copytree(CSS_SRC, dst_css, dirs_exist_ok=True)
        print(f"Copied CSS → {dst_css}/")

    js_files = [f for f in JS_SRC.iterdir()
                if f.name != ".gitkeep"] if JS_SRC.is_dir() else []
    if js_files:
        dst_js = output_dir / "js"
        shutil.copytree(JS_SRC, dst_js, dirs_exist_ok=True,
                        ignore=shutil.ignore_patterns(".gitkeep"))
        print(f"Copied JS → {dst_js}/")

    font_files = [f for f in FONTS_SRC.iterdir()
                  if f.name != ".gitkeep"] if FONTS_SRC.is_dir() else []
    if font_files:
        dst_fonts = output_dir / "fonts"
        shutil.copytree(FONTS_SRC, dst_fonts, dirs_exist_ok=True,
                        ignore=shutil.ignore_patterns(".gitkeep"))
        print(f"Copied fonts → {dst_fonts}/")

    for fname in ["LICENSE.txt", "ATTRIBUTION.md"]:
        src_file = REPO_ROOT / fname
        if src_file.exists():
            shutil.copy(src_file, output_dir / fname)

    # ── Validate ──────────────────────────────────────────────────────────────

    print("Validating output for external resource URLs...")
    violations = validate_no_external_resources(output_dir)
    if violations:
        print("ERROR: External resource URLs found in output HTML:",
              file=sys.stderr)
        for v in violations:
            print(f"  {v}", file=sys.stderr)
        print("The overlay must not introduce external <link> or <script> "
              "dependencies.", file=sys.stderr)
        sys.exit(1)

    print("Validation passed: no external resource URLs in output.")
    print("Done.")


if __name__ == "__main__":
    main()
