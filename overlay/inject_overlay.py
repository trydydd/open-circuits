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
LOGO_SRC = OVERLAY_DIR / "logo.svg"

TEMPLATE_KEYS = [
    "INDEX_PATH",
    "VOL_DC", "VOL_AC", "VOL_SEMI", "VOL_DIGITAL", "VOL_REF", "VOL_EXPER",
    "VOL_DC_IDX", "VOL_AC_IDX", "VOL_SEMI_IDX", "VOL_DIGITAL_IDX", "VOL_REF_IDX", "VOL_EXPER_IDX",
    "LICENSE_PATH", "ATTRIBUTION_PATH",
    "JS_PATH", "LOGO_PATH", "LOGO_SVG",
]

# Upstream pages include hosting/validation badge links from these domains
_BADGE_DOMAINS_RE = re.compile(r"ibiblio\.org|validator\.w3\.org|gnu\.org", re.IGNORECASE)


def _load_inline_logo() -> str:
    """Read logo.svg and prepare it for inline HTML use."""
    svg = LOGO_SRC.read_text(encoding="utf-8").strip()
    return re.sub(
        r"^<svg\b",
        '<svg class="oc-logo" aria-hidden="true" focusable="false"',
        svg,
        count=1,
    )


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
        "LOGO_PATH":        f"{p}logo.svg",
        "LOGO_SVG":         _load_inline_logo(),
        "VOL_DC_IDX":       f"{p}DC/index.html",
        "VOL_AC_IDX":       f"{p}AC/index.html",
        "VOL_SEMI_IDX":     f"{p}Semi/index.html",
        "VOL_DIGITAL_IDX":  f"{p}Digital/index.html",
        "VOL_REF_IDX":      f"{p}Ref/index.html",
        "VOL_EXPER_IDX":    f"{p}Exper/index.html",
    }


def _strip_badge_links(content: str) -> str:
    """Remove upstream hosting/validation badge <a> links from page content."""
    return re.sub(
        r'<a\b[^>]*\bhref=["\'][^"\']*(?:ibiblio\.org|validator\.w3\.org|gnu\.org)[^"\']*["\'][^>]*>.*?</a\s*>',
        '',
        content,
        flags=re.IGNORECASE | re.DOTALL,
    )


def _strip_download_sections(content: str) -> str:
    """Remove download link sections from volume index pages and the main index.

    Volume index pages have two sections delimited by <!--!!!--> comment markers:
    'Download printable versions of this volume' (PDF/PostScript) and
    'Download source files for this volume' (tar archives). Both are removed,
    leaving only the 'Back to Master Index' link that follows.

    The main index (index.htm) contains several download/free-software sections
    similarly delimited. All are removed; the ibiblio hosted-badge link that
    follows is handled separately by _strip_badge_links.
    """
    # Volume index: strip from <!--!!!--> before "Download printable versions"
    # through end of source section, stopping before the trailing <hr> + "Back to".
    content = re.sub(
        r'<!--!{5,}-->\s*<hr>\s*<h2>\s*Download\s+printable\s+versions\b'
        r'.*?'
        r'(?=<hr>\s*<a\b[^>]*>Back\s+to\b)',
        '',
        content,
        flags=re.IGNORECASE | re.DOTALL,
    )
    # Main index: each download/software section starts with <!--!!!--> + <hr> + <h2>.
    # Strip each such section up to (but not including) the next <!--!!!--> marker.
    # Repeated substitution cascades through all adjacent sections in one pass.
    content = re.sub(
        r'<!--!{5,}-->\s*<hr>\s*<h2>\s*(?:Download|Some\s+of\s+the\s+free\s+software)\b'
        r'.*?'
        r'(?=<!--!{5,}-->)',
        '',
        content,
        flags=re.IGNORECASE | re.DOTALL,
    )
    return content


def _strip_local_binary_links(content: str) -> str:
    """De-link <a href> tags pointing to local binary or archive files.

    Removes the anchor wrapper but keeps the visible link text. Only affects
    relative hrefs ending in known binary extensions — external URLs, fragment
    links, and domain-like relative paths (e.g. photochemistry.epfl.ch/…) are
    left untouched.
    """
    return re.sub(
        r'<a\b[^>]*\bhref=["\']'
        r'(?!https?://|#|mailto:)'
        r'(?![a-z0-9-]+(?:\.[a-z0-9-]+)+/)'
        r'[^"\']*\.(pdf|ps\.gz|ps|tar\.gz|tar|exe|zip|ovl)'
        r'["\'][^>]*>'
        r'(.*?)'
        r'</a\s*>',
        r'\2',
        content,
        flags=re.IGNORECASE | re.DOTALL,
    )


def _extract_chapter_title(content: str) -> str | None:
    """Extract chapter title from <meta name="description" content="...">."""
    m = re.search(
        r'<meta\s+name=["\']description["\']\s+content=["\']([^"\']+)["\']',
        content, re.IGNORECASE,
    )
    if m:
        return m.group(1).strip() or None
    return None


def _strip_volume_title(content: str) -> str:
    """Remove the redundant 'Lessons In Electric Circuits' volume heading near the top of body."""
    body_match = re.search(r'<body[^>]*>', content, re.IGNORECASE)
    if not body_match:
        return content

    body_start = body_match.end()
    # 500 bytes covers the opening of every Kuphaldt page; the volume title
    # always appears within the first few tags. Searching the full body would
    # risk matching legitimate occurrences deeper in the chapter text.
    window = content[body_start:body_start + 500]
    soup = BeautifulSoup(window, "html.parser")
    for tag in soup.find_all(["h1", "b"]):
        if re.search(r"Lessons\s+In\s+Electric\s+Circuits", tag.get_text(), re.IGNORECASE):
            tag_str = str(tag)
            idx = window.find(tag_str)
            if idx != -1:
                content = content[:body_start + idx] + content[body_start + idx + len(tag_str):]
            break

    return content


def render_template(tmpl_path: Path, subs: dict[str, str]) -> str:
    """Render a template by replacing {{KEY}} tokens with values from subs.

    Unknown keys are left in the output as-is, which makes template errors
    visible in the rendered HTML rather than silently empty.
    """
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
    content = _strip_download_sections(content)
    content = _strip_local_binary_links(content)
    content = _strip_volume_title(content)

    # Homepage: replace the entire body content with a curated template so we
    # don't carry forward any of the upstream project-admin prose.
    is_homepage = (src.name.lower() == "index.htm" and depth == 0)
    if is_homepage:
        index_body = render_template(TEMPLATES_DIR / "index-body.html", subs)
        content = re.sub(
            r'(<body[^>]*>).*?(</body>)',
            lambda m: m.group(1) + "\n" + index_body + "\n" + m.group(2),
            content, count=1, flags=re.IGNORECASE | re.DOTALL,
        )
        content = re.sub(
            r"<title>[^<]*</title>",
            "<title>Open Circuits \u2014 Lessons in Electric Circuits</title>",
            content, count=1, flags=re.IGNORECASE,
        )

    # Rewrite page title using meta description (most chapters have a meaningful one),
    # falling back to the colophon-style upstream title, then bare "Open Circuits".
    if not is_homepage:
        chapter_title = _extract_chapter_title(content)
        if chapter_title:
            content = re.sub(
                r"<title>[^<]*</title>",
                f"<title>Open Circuits \u2014 {chapter_title}</title>",
                content, count=1, flags=re.IGNORECASE,
            )
        else:
            # Try to extract a meaningful subtitle from "... -- Chapter N: Title"
            content = re.sub(
                r"<title>Lessons In Electric Circuits[^<]*?:\s*([^<]+)</title>",
                "<title>Open Circuits \u2014 \\g<1></title>",
                content, flags=re.IGNORECASE,
            )
            # Final fallback
            content = re.sub(
                r"<title>Lessons In Electric Circuits[^<]*</title>",
                "<title>Open Circuits</title>",
                content, flags=re.IGNORECASE,
            )

    # Add lang="en" to <html> tag if not already present
    content = re.sub(
        r'(<html)(?![^>]*\blang=)([^>]*>)',
        r'\1 lang="en"\2',
        content, count=1, flags=re.IGNORECASE,
    )

    # Strip inline background-color styles and presentational border attributes
    # from <table> tags — Kuphaldt uses hardcoded #E0FFFF that breaks dark mode.
    content = re.sub(
        r'(<table)([^>]*)(>)',
        lambda m: m.group(1) + re.sub(
            r'\s*(?:style|border)\s*=\s*(?:"[^"]*"|\'[^\']*\'|\S+)',
            '',
            m.group(2),
            flags=re.IGNORECASE,
        ) + m.group(3),
        content,
        flags=re.IGNORECASE,
    )

    # Insert viewport meta, CSS link, and JS script before </head> (case-insensitive)
    content, n = re.subn(
        r"(</head>)", f"{viewport}\n{css_link}\n{js_tag}\n\\1", content, count=1, flags=re.IGNORECASE
    )
    if n == 0:
        # No </head> found — shouldn't occur in Kuphaldt's files, but prepend
        # as a safety net so the page still gets CSS and the viewport tag.
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

    if LOGO_SRC.exists():
        shutil.copy2(LOGO_SRC, output_dir / "logo.svg")
        print(f"Copied logo → {output_dir / 'logo.svg'}")

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
