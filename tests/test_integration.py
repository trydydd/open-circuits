"""
End-to-end integration tests for Open Circuits, Phases 1–4.

Runs the full pipeline against real upstream data — no mocks, no synthetic
pages.  Requires internet access to download the Kuphaldt HTML bundle from
ibiblio.org on first run (~36 MB).  Subsequent runs reuse upstream/html/.

Run:
    pytest tests/                        # full suite
    pytest tests/ -k "phase1"           # one phase
    pytest tests/ -v                     # verbose
"""

import re
import subprocess
import sys
from pathlib import Path

import pytest
from bs4 import BeautifulSoup

REPO_ROOT = Path(__file__).parent.parent
PYTHON = sys.executable


# ── Helpers ───────────────────────────────────────────────────────────────────

def run(script, *args):
    return subprocess.run(
        [PYTHON, str(script), *args],
        capture_output=True, text=True, cwd=REPO_ROOT,
    )


# ── Phase 1: Foundation ───────────────────────────────────────────────────────

class TestPhase1Foundation:
    def test_upstream_dir_exists(self):
        assert (REPO_ROOT / "upstream").is_dir()

    def test_build_dir_exists(self):
        assert (REPO_ROOT / "build").is_dir()

    def test_overlay_css_dir_exists(self):
        assert (REPO_ROOT / "overlay" / "css").is_dir()

    def test_overlay_js_dir_exists(self):
        assert (REPO_ROOT / "overlay" / "js").is_dir()

    def test_overlay_templates_dir_exists(self):
        assert (REPO_ROOT / "overlay" / "templates").is_dir()

    def test_output_dir_exists(self):
        assert (REPO_ROOT / "output").is_dir()

    def test_zim_metadata_dir_exists(self):
        assert (REPO_ROOT / "zim-metadata").is_dir()

    def test_github_workflows_dir_exists(self):
        assert (REPO_ROOT / ".github" / "workflows").is_dir()

    def test_docs_dir_exists(self):
        assert (REPO_ROOT / "docs").is_dir()

    def test_license_txt_nonempty(self):
        f = REPO_ROOT / "LICENSE.txt"
        assert f.exists() and f.stat().st_size > 0

    def test_license_txt_identifies_cc_by_40(self):
        text = (REPO_ROOT / "LICENSE.txt").read_text()
        assert "Creative Commons" in text
        assert "4.0" in text

    def test_attribution_md_nonempty(self):
        f = REPO_ROOT / "ATTRIBUTION.md"
        assert f.exists() and f.stat().st_size > 0

    def test_attribution_md_credits_kuphaldt(self):
        text = (REPO_ROOT / "ATTRIBUTION.md").read_text()
        assert "Kuphaldt" in text

    def test_attribution_md_references_cc_by(self):
        text = (REPO_ROOT / "ATTRIBUTION.md").read_text()
        assert "Creative Commons" in text or "CC BY" in text

    def test_readme_nonempty(self):
        f = REPO_ROOT / "README.md"
        assert f.exists() and f.stat().st_size > 0

    def test_output_gitignore_exists(self):
        assert (REPO_ROOT / "output" / ".gitignore").exists()


# ── Phase 2: Download pipeline ────────────────────────────────────────────────

class TestPhase2Download:
    def test_upstream_html_created(self, upstream_html):
        assert upstream_html.is_dir()

    @pytest.mark.parametrize("volume", ["DC", "AC", "Semi", "Digital", "Ref", "Exper"])
    def test_volume_directory_exists(self, upstream_html, volume):
        assert (upstream_html / volume).is_dir()

    def test_upstream_html_contains_html_files(self, upstream_html):
        files = list(upstream_html.rglob("*.html"))
        assert len(files) > 0

    def test_upstream_version_txt_has_source_url(self):
        text = (REPO_ROOT / "upstream" / "UPSTREAM-VERSION.txt").read_text()
        assert re.search(r"^SOURCE_URL=", text, re.MULTILINE)

    def test_upstream_version_txt_has_snapshot_date(self):
        text = (REPO_ROOT / "upstream" / "UPSTREAM-VERSION.txt").read_text()
        assert re.search(r"^SNAPSHOT_DATE=\d{4}-\d{2}-\d{2}", text, re.MULTILINE)

    def test_download_is_idempotent(self):
        result = run(REPO_ROOT / "build" / "download_source.py")
        assert result.returncode == 0
        assert "already populated" in result.stdout

    def test_dc_first_chapter_exists(self, upstream_html):
        assert (upstream_html / "DC" / "DC_1.html").exists()


# ── Phase 3: Overlay assets ───────────────────────────────────────────────────

class TestPhase3OverlayAssets:
    def test_css_file_exists(self):
        assert (REPO_ROOT / "overlay" / "css" / "open-circuits.css").exists()

    def test_css_contains_no_external_urls(self):
        text = (REPO_ROOT / "overlay" / "css" / "open-circuits.css").read_text()
        assert not re.search(r"https?://", text)

    def test_css_defines_max_width(self):
        text = (REPO_ROOT / "overlay" / "css" / "open-circuits.css").read_text()
        assert "max-width" in text

    def test_css_defines_oc_header(self):
        text = (REPO_ROOT / "overlay" / "css" / "open-circuits.css").read_text()
        assert "oc-header" in text

    def test_css_defines_oc_footer(self):
        text = (REPO_ROOT / "overlay" / "css" / "open-circuits.css").read_text()
        assert "oc-footer" in text

    def test_css_has_responsive_media_query(self):
        text = (REPO_ROOT / "overlay" / "css" / "open-circuits.css").read_text()
        assert "@media" in text

    def test_header_template_exists(self):
        assert (REPO_ROOT / "overlay" / "templates" / "header.html").exists()

    @pytest.mark.parametrize("placeholder", [
        "INDEX_PATH", "VOL_DC", "VOL_AC", "VOL_SEMI",
        "VOL_DIGITAL", "VOL_REF", "VOL_EXPER",
    ])
    def test_header_template_has_placeholder(self, placeholder):
        text = (REPO_ROOT / "overlay" / "templates" / "header.html").read_text()
        assert "{{" + placeholder + "}}" in text

    def test_footer_template_exists(self):
        assert (REPO_ROOT / "overlay" / "templates" / "footer.html").exists()

    def test_footer_template_has_license_placeholder(self):
        text = (REPO_ROOT / "overlay" / "templates" / "footer.html").read_text()
        assert "{{LICENSE_PATH}}" in text

    def test_footer_template_has_attribution_placeholder(self):
        text = (REPO_ROOT / "overlay" / "templates" / "footer.html").read_text()
        assert "{{ATTRIBUTION_PATH}}" in text


# ── Phase 4: Overlay injection ────────────────────────────────────────────────

class TestPhase4Injection:
    def test_inject_script_exists(self):
        assert (REPO_ROOT / "overlay" / "inject_overlay.py").exists()

    def test_output_dir_created(self, output_html):
        assert output_html.is_dir()

    @pytest.mark.parametrize("volume", ["DC", "AC", "Semi", "Digital", "Ref", "Exper"])
    def test_volume_directory_exists_in_output(self, output_html, volume):
        assert (output_html / volume).is_dir()

    def test_output_has_at_least_as_many_pages_as_input(self, upstream_html, output_html):
        n_in = len(list(upstream_html.rglob("*.html")))
        n_out = len(list(output_html.rglob("*.html")))
        assert n_out >= n_in

    def test_css_copied_to_output(self, output_html):
        assert (output_html / "css" / "open-circuits.css").exists()

    def test_license_copied_to_output(self, output_html):
        assert (output_html / "LICENSE.txt").exists()

    def test_attribution_copied_to_output(self, output_html):
        assert (output_html / "ATTRIBUTION.md").exists()

    def test_dc_first_chapter_in_output(self, output_html):
        assert (output_html / "DC" / "DC_1.html").exists()

    def test_css_link_in_root_page(self, output_html):
        page = next(output_html.glob("*.html"))
        assert '<link rel="stylesheet" href="css/open-circuits.css">' in page.read_text()

    def test_css_link_depth_relative_in_subdir_page(self, output_html):
        page = next(output_html.rglob("DC/*.html"))
        assert '<link rel="stylesheet" href="../css/open-circuits.css">' in page.read_text()

    def test_oc_header_injected(self, output_html):
        page = next(output_html.rglob("DC/*.html"))
        assert 'class="oc-header"' in page.read_text()

    def test_oc_footer_injected(self, output_html):
        page = next(output_html.rglob("DC/*.html"))
        assert 'class="oc-footer"' in page.read_text()

    def test_root_page_has_no_dotdot_css_prefix(self, output_html):
        page = next(output_html.glob("*.html"))
        assert 'href="../css/' not in page.read_text()

    def test_subdir_page_index_link_goes_up(self, output_html):
        page = next(output_html.rglob("DC/*.html"))
        assert 'href="../index.html"' in page.read_text()

    def test_subdir_page_vol_nav_has_dotdot_prefix(self, output_html):
        page = next(output_html.rglob("DC/*.html"))
        assert 'href="../DC/DC_1.html"' in page.read_text()

    def test_subdir_footer_links_use_dotdot(self, output_html):
        page = next(output_html.rglob("DC/*.html"))
        text = page.read_text()
        assert 'href="../LICENSE.txt"' in text
        assert 'href="../ATTRIBUTION.md"' in text

    def test_root_footer_links_use_bare_paths(self, output_html):
        page = next(output_html.glob("*.html"))
        text = page.read_text()
        assert 'href="LICENSE.txt"' in text
        assert 'href="ATTRIBUTION.md"' in text

    def test_header_appears_before_footer_on_every_page(self, output_html):
        for page in output_html.rglob("*.html"):
            text = page.read_text()
            h = text.find('class="oc-header"')
            f = text.find('class="oc-footer"')
            assert h != -1 and f != -1 and h < f, \
                f"Header/footer ordering wrong in {page.relative_to(output_html)}"

    def test_validator_rejects_external_link_resource(self, tmp_path):
        inp = tmp_path / "in"
        out = tmp_path / "out"
        inp.mkdir()
        (inp / "bad.html").write_text(
            '<html><head>'
            '<link rel="stylesheet" href="https://cdn.example.com/bad.css">'
            '</head><body><p>Hi</p></body></html>'
        )
        result = run(REPO_ROOT / "overlay" / "inject_overlay.py", str(inp), str(out))
        assert result.returncode != 0
        assert "External resource URLs" in result.stderr

    def test_validator_rejects_external_script_resource(self, tmp_path):
        inp = tmp_path / "in"
        out = tmp_path / "out"
        inp.mkdir()
        (inp / "bad.html").write_text(
            '<html><head></head>'
            '<body><script src="https://cdn.example.com/track.js"></script>'
            '<p>Hi</p></body></html>'
        )
        result = run(REPO_ROOT / "overlay" / "inject_overlay.py", str(inp), str(out))
        assert result.returncode != 0

    def test_validator_passes_external_anchor_href(self, tmp_path):
        inp = tmp_path / "in"
        out = tmp_path / "out"
        inp.mkdir()
        (inp / "ok.html").write_text(
            '<html><head><title>T</title></head>'
            '<body><p>See <a href="https://www.ibiblio.org/">ibiblio</a>.</p>'
            '</body></html>'
        )
        result = run(REPO_ROOT / "overlay" / "inject_overlay.py", str(inp), str(out))
        assert result.returncode == 0

    def test_inject_fails_without_arguments(self):
        result = run(REPO_ROOT / "overlay" / "inject_overlay.py")
        assert result.returncode != 0

    def test_inject_fails_with_nonexistent_input(self, tmp_path):
        result = run(REPO_ROOT / "overlay" / "inject_overlay.py",
                     "/no/such/dir", str(tmp_path / "out"))
        assert result.returncode != 0


# ── Content integrity ─────────────────────────────────────────────────────────

class TestContentIntegrity:
    def test_integrity_script_exists(self):
        assert (REPO_ROOT / "build" / "verify_content_integrity.py").exists()

    def test_passes_on_real_output(self, upstream_html, output_html):
        result = run(
            REPO_ROOT / "build" / "verify_content_integrity.py",
            str(upstream_html), str(output_html),
        )
        assert result.returncode == 0
        assert "INTEGRITY CHECK PASSED" in result.stdout

    def test_reports_correct_page_count(self, upstream_html, output_html):
        page_count = len(list(upstream_html.rglob("*.html")))
        result = run(
            REPO_ROOT / "build" / "verify_content_integrity.py",
            str(upstream_html), str(output_html),
        )
        assert result.returncode == 0
        assert f"{page_count} passed" in result.stdout

    def test_detects_tampered_text(self, tmp_path):
        inp = tmp_path / "in"
        out = tmp_path / "out"
        inp.mkdir()
        (inp / "index.html").write_text(
            "<html><head><title>T</title></head>"
            "<body><p>Original text here.</p></body></html>"
        )
        run(REPO_ROOT / "overlay" / "inject_overlay.py", str(inp), str(out))
        tampered = out / "index.html"
        tampered.write_text(tampered.read_text().replace("Original", "TAMPERED"))

        result = run(REPO_ROOT / "build" / "verify_content_integrity.py",
                     str(inp), str(out))
        assert result.returncode != 0
        assert "FAIL" in result.stdout

    def test_diff_flag_shows_changed_tokens(self, tmp_path):
        inp = tmp_path / "in"
        out = tmp_path / "out"
        inp.mkdir()
        (inp / "index.html").write_text(
            "<html><head></head><body><p>Hello world.</p></body></html>"
        )
        run(REPO_ROOT / "overlay" / "inject_overlay.py", str(inp), str(out))
        tampered = out / "index.html"
        tampered.write_text(tampered.read_text().replace("Hello", "Goodbye"))

        result = run(REPO_ROOT / "build" / "verify_content_integrity.py",
                     "--diff", str(inp), str(out))
        assert result.returncode != 0
        assert "Hello" in result.stdout or "Goodbye" in result.stdout

    def test_detects_missing_output_page(self, tmp_path):
        inp = tmp_path / "in"
        out = tmp_path / "out"
        (inp / "sub").mkdir(parents=True)
        (inp / "index.html").write_text(
            "<html><head></head><body><p>Root.</p></body></html>"
        )
        (inp / "sub" / "page.html").write_text(
            "<html><head></head><body><p>Sub.</p></body></html>"
        )
        run(REPO_ROOT / "overlay" / "inject_overlay.py", str(inp), str(out))
        (out / "sub" / "page.html").unlink()

        result = run(REPO_ROOT / "build" / "verify_content_integrity.py",
                     str(inp), str(out))
        assert result.returncode != 0
        assert "MISSING" in result.stdout

    def test_fails_with_missing_upstream_dir(self, tmp_path):
        result = run(REPO_ROOT / "build" / "verify_content_integrity.py",
                     "/no/such/dir", str(tmp_path))
        assert result.returncode != 0

    def test_fails_with_missing_output_dir(self, upstream_html, tmp_path):
        result = run(REPO_ROOT / "build" / "verify_content_integrity.py",
                     str(upstream_html), str(tmp_path / "nonexistent"))
        assert result.returncode != 0
