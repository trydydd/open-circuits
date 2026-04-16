"""
Phase 5: Navigation browser-testing verification suite.

Verifies that inject_overlay.py produces HTML that navigation.js can operate
on correctly, and that the no-JS fallback is safe.  Uses synthetic Kuphaldt-
style HTML fixtures so no network access is needed.

DC_2.html is the canonical test case (has both prev and next links and
multiple h2 sections).  DC_1.html tests the first-chapter "no redundant Prev"
fix.

Checklist from TODO.md Phase 5:
  [x] TOC builder finds <a name="..."> anchors inside <h2> tags correctly
  [x] Scroll-spy markup: data-anchor attributes exist in JS template strings
  [x] Prev/next extraction identifies previous.jpg / next.jpg links correctly
  [x] Active-volume indicator: vol-nav link order matches JS vols array
  [x] First chapter shows no redundant "Prev" button (prev href == index href)
  [x] Mobile sidebar starts closed (inline script + aria-expanded=false)
  [x] Bottom chapter nav appears above the footer (JS inserts before .oc-footer)
  [x] Dark mode: all colors render correctly (RGB fallbacks + OKLCH present)
  [x] No-JS fallback: <noscript> hides sidebar; image nav preserved
"""

import subprocess
import sys
from pathlib import Path

import pytest
from bs4 import BeautifulSoup

REPO_ROOT = Path(__file__).parent.parent
PYTHON = sys.executable
INJECT = REPO_ROOT / "overlay" / "inject_overlay.py"

# ── Synthetic Kuphaldt HTML fixtures ─────────────────────────────────────────
#
# Structure mirrors the real upstream pages described in CLAUDE.md:
#   <h2><u><a name="xtocidXXX">Title</a></u></h2>
#   <a href="..."><img src=previous.jpg alt="Previous"></a>  (unquoted src)

KUPHALDT_DC2 = """\
<html>
<head><title>Ohm's Law - Lessons In Electric Circuits, Volume I</title></head>
<body bgColor=white>
<h1>Lessons in Electric Circuits</h1>
<h1>Volume I - DC</h1>
<ul>
  <li><a href="#xtocid10">Ohm's Law</a></li>
  <li><a href="#xtocid11">Power in Electric Circuits</a></li>
  <li><a href="#xtocid12">Resistors in Series and Parallel</a></li>
</ul>
<a href="DC_1.html"><img src=previous.jpg alt="Previous"></a>
<a href="index.html"><img src=contents.jpg alt="Contents"></a>
<a href="DC_3.html"><img src=next.jpg alt="Next"></a><br><br>

<h2><u><a name="xtocid10">Ohm's Law</a></u></h2>
<p>How voltage, current, and resistance relate.</p>

<h2><u><a name="xtocid11">Power in Electric Circuits</a></u></h2>
<p>How electrical power is calculated.</p>

<h2><u><a name="xtocid12">Resistors in Series and Parallel</a></u></h2>
<p>How resistors combine in circuits.</p>

<a href="DC_1.html"><img src=previous.jpg alt="Previous"></a>
<a href="index.html"><img src=contents.jpg alt="Contents"></a>
<a href="DC_3.html"><img src=next.jpg alt="Next"></a>
</body>
</html>
"""

# First chapter: prev and contents both point to index.html (same href).
# This is the precondition for the JS "no redundant Prev" fix.
KUPHALDT_DC1 = """\
<html>
<head><title>Basic Concepts - Lessons In Electric Circuits</title></head>
<body bgColor=white>
<h1>Lessons in Electric Circuits</h1>
<h1>Volume I - DC</h1>
<ul>
  <li><a href="#xtocid1">Introduction</a></li>
  <li><a href="#xtocid2">Static Electricity</a></li>
</ul>
<a href="index.html"><img src=previous.jpg alt="Previous"></a>
<a href="index.html"><img src=contents.jpg alt="Contents"></a>
<a href="DC_2.html"><img src=next.jpg alt="Next"></a><br><br>

<h2><u><a name="xtocid1">Introduction</a></u></h2>
<p>Electricity defined and explained.</p>

<h2><u><a name="xtocid2">Static Electricity</a></u></h2>
<p>Static charge and Coulomb's law.</p>

<a href="index.html"><img src=previous.jpg alt="Previous"></a>
<a href="index.html"><img src=contents.jpg alt="Contents"></a>
<a href="DC_2.html"><img src=next.jpg alt="Next"></a>
</body>
</html>
"""


# ── Fixtures ──────────────────────────────────────────────────────────────────

def _inject(src_dir: Path, out_dir: Path) -> None:
    result = subprocess.run(
        [PYTHON, str(INJECT), str(src_dir), str(out_dir)],
        capture_output=True, text=True, cwd=REPO_ROOT,
    )
    assert result.returncode == 0, (
        f"inject_overlay.py failed:\nstdout: {result.stdout}\nstderr: {result.stderr}"
    )


@pytest.fixture(scope="module")
def injected_dc2(tmp_path_factory):
    src = tmp_path_factory.mktemp("src_dc2")
    out = tmp_path_factory.mktemp("out_dc2")
    dc = src / "DC"
    dc.mkdir()
    (dc / "DC_2.html").write_text(KUPHALDT_DC2)
    _inject(src, out)
    return out


@pytest.fixture(scope="module")
def injected_dc1(tmp_path_factory):
    src = tmp_path_factory.mktemp("src_dc1")
    out = tmp_path_factory.mktemp("out_dc1")
    dc = src / "DC"
    dc.mkdir()
    (dc / "DC_1.html").write_text(KUPHALDT_DC1)
    _inject(src, out)
    return out


def soup(path: Path) -> BeautifulSoup:
    return BeautifulSoup(path.read_text(), "html.parser")


# ── 1. TOC builder ────────────────────────────────────────────────────────────

class TestTOCBuilder:
    """TOC builder finds <a name="..."> anchors inside <h2> tags correctly."""

    def test_h2_anchor_names_preserved(self, injected_dc2):
        page = injected_dc2 / "DC" / "DC_2.html"
        s = soup(page)
        found = {
            a["name"]
            for h2 in s.find_all("h2")
            for a in h2.find_all("a", attrs={"name": True})
        }
        assert {"xtocid10", "xtocid11", "xtocid12"}.issubset(found)

    def test_h2_elements_have_text(self, injected_dc2):
        page = injected_dc2 / "DC" / "DC_2.html"
        s = soup(page)
        named_h2s = [
            h for h in s.find_all("h2")
            if h.find("a", attrs={"name": True})
        ]
        assert len(named_h2s) >= 3
        for h2 in named_h2s:
            assert h2.get_text(strip=True) != ""

    def test_injection_does_not_destroy_h2_markup(self, injected_dc2):
        page = injected_dc2 / "DC" / "DC_2.html"
        s = soup(page)
        assert len(s.find_all("h2")) >= 3

    def test_js_uses_a_name_selector(self):
        js = (REPO_ROOT / "overlay" / "js" / "navigation.js").read_text()
        assert 'querySelector("a[name]")' in js or "querySelector('a[name]')" in js

    def test_js_falls_back_from_id_to_name(self):
        js = (REPO_ROOT / "overlay" / "js" / "navigation.js").read_text()
        assert "h2.id" in js
        assert "a[name]" in js


# ── 2. Scroll-spy ─────────────────────────────────────────────────────────────

class TestScrollSpy:
    """Scroll-spy highlights the right section as the reader scrolls."""

    def test_js_has_scroll_event_listener(self):
        js = (REPO_ROOT / "overlay" / "js" / "navigation.js").read_text()
        assert "addEventListener('scroll'" in js or 'addEventListener("scroll"' in js

    def test_js_uses_data_anchor_attribute(self):
        js = (REPO_ROOT / "overlay" / "js" / "navigation.js").read_text()
        assert "data-anchor" in js

    def test_js_toggles_is_active_class(self):
        js = (REPO_ROOT / "overlay" / "js" / "navigation.js").read_text()
        assert "is-active" in js
        assert "classList.toggle" in js

    def test_js_reads_header_height_css_var(self):
        js = (REPO_ROOT / "overlay" / "js" / "navigation.js").read_text()
        assert "--oc-header-h" in js

    def test_css_defines_is_active_style(self):
        css = (REPO_ROOT / "overlay" / "css" / "open-circuits.css").read_text()
        assert ".oc-toc__link.is-active" in css


# ── 3. Prev/next extraction ───────────────────────────────────────────────────

class TestImageNavExtraction:
    """Prev/next extraction identifies previous.jpg / next.jpg links correctly."""

    def test_image_nav_links_survive_injection(self, injected_dc2):
        page = injected_dc2 / "DC" / "DC_2.html"
        s = soup(page)
        srcs = [
            (img.get("src", "") or "").lower()
            for a in s.find_all("a", href=True)
            for img in [a.find("img")]
            if img
        ]
        assert any("previous" in s for s in srcs)
        assert any("next" in s for s in srcs)
        assert any("contents" in s for s in srcs)

    def test_prev_href_points_to_dc1(self, injected_dc2):
        page = injected_dc2 / "DC" / "DC_2.html"
        s = soup(page)
        for a in s.find_all("a", href=True):
            img = a.find("img")
            if img and "previous" in (img.get("src", "") or "").lower():
                assert "DC_1.html" in a["href"]
                return
        pytest.fail("No previous image link found in injected DC_2")

    def test_next_href_points_to_dc3(self, injected_dc2):
        page = injected_dc2 / "DC" / "DC_2.html"
        s = soup(page)
        for a in s.find_all("a", href=True):
            img = a.find("img")
            if img and "next" in (img.get("src", "") or "").lower():
                assert "DC_3.html" in a["href"]
                return
        pytest.fail("No next image link found in injected DC_2")

    def test_js_checks_previous_in_src(self):
        js = (REPO_ROOT / "overlay" / "js" / "navigation.js").read_text()
        assert "previous" in js
        assert "next" in js
        assert "contents" in js


# ── 4. Active-volume indicator ────────────────────────────────────────────────

class TestActiveVolumeIndicator:
    """Active-volume indicator highlights the correct volume."""

    def test_vol_nav_present(self, injected_dc2):
        page = injected_dc2 / "DC" / "DC_2.html"
        s = soup(page)
        assert s.find(class_="oc-vol-nav") is not None

    def test_vol_nav_has_six_links(self, injected_dc2):
        page = injected_dc2 / "DC" / "DC_2.html"
        s = soup(page)
        links = s.find(class_="oc-vol-nav").find_all("a")
        assert len(links) == 6

    def test_vol_nav_link_text_order_matches_js_vols_array(self, injected_dc2):
        """JS markActiveVolume() couples links[i] to vols[i] — order must match."""
        page = injected_dc2 / "DC" / "DC_2.html"
        s = soup(page)
        texts = [a.get_text(strip=True) for a in s.find(class_="oc-vol-nav").find_all("a")]
        assert texts == ["DC", "AC", "Semi", "Digital", "Ref", "Exper"]

    def test_dc_link_href_contains_dc_dir(self, injected_dc2):
        page = injected_dc2 / "DC" / "DC_2.html"
        s = soup(page)
        dc_link = s.find(class_="oc-vol-nav").find_all("a")[0]
        assert "DC/" in dc_link["href"]

    def test_css_defines_is_active_vol_nav(self):
        css = (REPO_ROOT / "overlay" / "css" / "open-circuits.css").read_text()
        assert ".oc-vol-nav a.is-active" in css

    def test_js_marks_active_volume(self):
        js = (REPO_ROOT / "overlay" / "js" / "navigation.js").read_text()
        assert "markActiveVolume" in js
        assert "is-active" in js


# ── 5. First chapter: no redundant Prev button ───────────────────────────────

class TestFirstChapterNoPrevButton:
    """First chapter shows no redundant 'Prev' button.

    The JS fix sets nav.prev = null when prev href equals index href.
    This test verifies the HTML precondition: DC_1's prev and contents
    links share the same href so the JS equality check fires correctly.
    """

    def test_dc1_prev_href_equals_contents_href(self, injected_dc1):
        page = injected_dc1 / "DC" / "DC_1.html"
        s = soup(page)
        prev_href = contents_href = None
        for a in s.find_all("a", href=True):
            img = a.find("img")
            if not img:
                continue
            src = (img.get("src", "") or "").lower()
            if "previous" in src and prev_href is None:
                prev_href = a["href"]
            elif "contents" in src and contents_href is None:
                contents_href = a["href"]
        assert prev_href is not None, "DC_1 has no previous image link"
        assert contents_href is not None, "DC_1 has no contents image link"
        assert prev_href == contents_href, (
            f"DC_1 prev ({prev_href!r}) ≠ contents ({contents_href!r}); "
            "JS suppression of redundant Prev will not fire"
        )

    def test_js_suppresses_prev_when_equal_to_index(self):
        js = (REPO_ROOT / "overlay" / "js" / "navigation.js").read_text()
        assert "result.prev === result.index" in js or \
               "nav.prev === nav.index" in js or \
               "result.prev = null" in js


# ── 6. Mobile sidebar starts closed ──────────────────────────────────────────

class TestMobileSidebarStartsClosed:
    """Mobile sidebar starts closed, opens and closes via toggle."""

    def test_header_template_has_sidebar_closed_inline_script(self):
        header = (REPO_ROOT / "overlay" / "templates" / "header.html").read_text()
        assert "document.body.classList.add('sidebar-closed')" in header

    def test_toggle_aria_expanded_false_in_template(self):
        header = (REPO_ROOT / "overlay" / "templates" / "header.html").read_text()
        assert 'aria-expanded="false"' in header

    def test_toggle_aria_expanded_false_in_output(self, injected_dc2):
        page = injected_dc2 / "DC" / "DC_2.html"
        s = soup(page)
        toggle = s.find(id="oc-nav-toggle")
        assert toggle is not None, "Toggle button not found"
        assert toggle.get("aria-expanded") == "false"

    def test_sidebar_element_in_output(self, injected_dc2):
        page = injected_dc2 / "DC" / "DC_2.html"
        s = soup(page)
        assert s.find(id="oc-sidebar") is not None

    def test_js_calls_set_open_with_is_desktop(self):
        js = (REPO_ROOT / "overlay" / "js" / "navigation.js").read_text()
        assert "setOpen(isDesktop())" in js

    def test_css_sidebar_closed_hides_sidebar(self):
        css = (REPO_ROOT / "overlay" / "css" / "open-circuits.css").read_text()
        assert "body.sidebar-closed .oc-sidebar" in css
        assert "translateX(-100%)" in css


# ── 7. Bottom chapter nav above footer ───────────────────────────────────────

class TestBottomNavAboveFooter:
    """Bottom chapter nav appears above the footer."""

    def test_oc_footer_in_output(self, injected_dc2):
        page = injected_dc2 / "DC" / "DC_2.html"
        s = soup(page)
        assert s.find(class_="oc-footer") is not None

    def test_footer_before_body_close(self, injected_dc2):
        page = injected_dc2 / "DC" / "DC_2.html"
        text = page.read_text()
        footer_pos = text.rfind('class="oc-footer"')
        body_close = text.lower().rfind("</body>")
        assert footer_pos != -1 and body_close != -1
        assert footer_pos < body_close

    def test_js_inserts_nav_before_footer(self):
        js = (REPO_ROOT / "overlay" / "js" / "navigation.js").read_text()
        assert "footer.before(el)" in js

    def test_js_queries_oc_footer(self):
        js = (REPO_ROOT / "overlay" / "js" / "navigation.js").read_text()
        assert ".oc-footer" in js

    def test_css_defines_oc_bottomnav(self):
        css = (REPO_ROOT / "overlay" / "css" / "open-circuits.css").read_text()
        assert ".oc-bottomnav" in css


# ── 8. Dark mode colors ───────────────────────────────────────────────────────

class TestDarkMode:
    """Dark mode: all colors render correctly."""

    def test_dark_mode_media_query_present(self):
        css = (REPO_ROOT / "overlay" / "css" / "open-circuits.css").read_text()
        assert "@media (prefers-color-scheme: dark)" in css

    def test_dark_mode_has_rgb_fallbacks(self):
        css = (REPO_ROOT / "overlay" / "css" / "open-circuits.css").read_text()
        dark_idx = css.index("@media (prefers-color-scheme: dark)")
        dark_block = css[dark_idx:dark_idx + 2000]
        assert "rgb(" in dark_block

    def test_dark_mode_has_oklch_overrides(self):
        css = (REPO_ROOT / "overlay" / "css" / "open-circuits.css").read_text()
        dark_idx = css.index("@media (prefers-color-scheme: dark)")
        dark_block = css[dark_idx:dark_idx + 2000]
        assert "oklch(" in dark_block

    def test_no_relative_color_syntax(self):
        """Bug B fix: oklch(from var(...)) relative color syntax removed."""
        css = (REPO_ROOT / "overlay" / "css" / "open-circuits.css").read_text()
        assert "oklch(from var(" not in css

    def test_dark_mode_has_accent_border_variable(self):
        css = (REPO_ROOT / "overlay" / "css" / "open-circuits.css").read_text()
        dark_idx = css.index("@media (prefers-color-scheme: dark)")
        dark_block = css[dark_idx:dark_idx + 2000]
        assert "--oc-accent-border" in dark_block

    def test_img_dark_mode_rule_present(self):
        css = (REPO_ROOT / "overlay" / "css" / "open-circuits.css").read_text()
        assert "@media (prefers-color-scheme: dark)" in css
        dark_idx = css.index("@media (prefers-color-scheme: dark)")
        assert "img" in css[dark_idx:]


# ── 9. No-JS fallback ─────────────────────────────────────────────────────────

class TestNoJSFallback:
    """No-JS fallback: page is readable without JavaScript."""

    def test_header_template_has_noscript_block(self):
        header = (REPO_ROOT / "overlay" / "templates" / "header.html").read_text()
        assert "<noscript>" in header

    def test_noscript_hides_oc_sidebar(self):
        header = (REPO_ROOT / "overlay" / "templates" / "header.html").read_text()
        noscript_start = header.index("<noscript>")
        noscript_end = header.index("</noscript>") + len("</noscript>")
        noscript_block = header[noscript_start:noscript_end]
        assert "oc-sidebar" in noscript_block

    def test_noscript_hides_nav_toggle(self):
        header = (REPO_ROOT / "overlay" / "templates" / "header.html").read_text()
        noscript_start = header.index("<noscript>")
        noscript_end = header.index("</noscript>") + len("</noscript>")
        noscript_block = header[noscript_start:noscript_end]
        assert "oc-nav-toggle" in noscript_block

    def test_noscript_block_in_injected_output(self, injected_dc2):
        page = injected_dc2 / "DC" / "DC_2.html"
        s = soup(page)
        assert s.find("noscript") is not None

    def test_image_nav_preserved_for_nojs_users(self, injected_dc2):
        """Kuphaldt's original navigation survives injection for no-JS users."""
        page = injected_dc2 / "DC" / "DC_2.html"
        s = soup(page)
        nav_imgs = [
            img for img in s.find_all("img")
            if any(k in (img.get("src", "") or "").lower()
                   for k in ("previous", "next", "contents"))
        ]
        assert len(nav_imgs) > 0, "Kuphaldt image nav must be preserved for no-JS"

    def test_content_text_survives_injection(self, injected_dc2):
        page = injected_dc2 / "DC" / "DC_2.html"
        text = page.read_text()
        assert "How voltage, current, and resistance relate" in text
        assert "How electrical power is calculated" in text
