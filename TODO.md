# Open Circuits — Bug Fix Phases

Audited from static code analysis and inspection of the v1.0.0 release tarball.
Live site (`https://trydydd.github.io/open-circuits/`) was not accessible during audit (403).

---

## Phase 1: Broken links ✓ done

**Bug — "Master index" links dead-end on every volume page**
Severity: High

Kuphaldt's upstream root index is `index.htm`. The build renames it to `index.html` but never
rewrites internal links that reference it. Every volume `index.html` has two occurrences of
`href="../index.htm"` that 404 on the deployed site.

Fix: added a `re.sub` pass in `inject_file()` that rewrites any local (non-`http://`) `href`
or `src` ending in `.htm` to `.html`.

Files: `overlay/inject_overlay.py:inject_file()`

---

## Phase 2: CSS browser compatibility

Three related issues in `overlay/css/open-circuits.css`. All pure CSS — no JS or template
changes needed.

**Bug A — OKLCH palette has no fallback colors**
Severity: Medium

Every color token uses `oklch()` with no `rgb()` fallback. `oklch()` requires Chrome 111+,
Firefox 113+, or Safari 15.4+. Older browsers (including many cheap Android WebViews) ignore
every `oklch()` value and fall back to UA defaults, stripping the entire color theme.

Given the project goal ("readable on a €30 Android phone"), this is a meaningful risk.

Fix: add `rgb()` fallback declarations immediately before each `oklch()` value in the `:root`
and `@media (prefers-color-scheme: dark)` blocks.

Files: `overlay/css/open-circuits.css:53–128`

---

**Bug B — CSS Relative Color Syntax has limited browser support**
Severity: Low

```css
.oc-bottomnav__index {
  border-color: oklch(from var(--oc-accent) l c h / 0.35) !important;
}
```

`oklch(from ...)` (CSS Relative Color Syntax) requires Chrome 119+, Firefox 128+, or
Safari 16.4+. On older browsers the declaration is ignored; the border renders at full opacity.

Fix: replace with a static `oklch()` value (or a CSS variable) that approximates 35% opacity,
removing the relative color syntax dependency.

Files: `overlay/css/open-circuits.css:654`

---

**Bug C — `color-mix(in oklch, ...)` table striping has limited support**
Severity: Low

```css
tr:nth-child(even) td {
  background: color-mix(in oklch, var(--oc-surface) 60%, var(--oc-bg) 40%);
}
```

`color-mix()` requires Chrome 111+, Firefox 113+, or Safari 16.2+. On older browsers even
rows lose their stripe and tables are harder to scan.

Fix: replace with a static fallback color (matching the visual midpoint of surface and bg) and
keep `color-mix()` as the progressive enhancement above it.

Files: `overlay/css/open-circuits.css:311`

---

## Phase 3: Layout and sidebar initialisation

Four related bugs caused by the sidebar's initial state not being set in HTML. Touches CSS and
one template.

**Bug A — Mobile sidebar flashes open before JS loads**
Severity: Medium

The CSS uses `body:not(.sidebar-closed) .oc-sidebar` to keep the sidebar visible on desktop.
On mobile this same rule wins over the default `transform: translateX(-100%)` because no
`sidebar-closed` class is present in the initial HTML:

```css
@media (max-width: 768px) {
  .oc-sidebar                            { transform: translateX(-100%); } /* hides */
  body:not(.sidebar-closed) .oc-sidebar  { transform: translateX(0);     } /* overrides */
}
```

Until JS runs and adds `sidebar-closed`, the sidebar is visible on mobile.

Fix: add `sidebar-closed` to the `<body>` class in the header template. JS already calls
`setOpen(isDesktop())` on init, which will remove it on desktop and leave it in place on
mobile — eliminating the flash without changing any JS logic.

Files: `overlay/templates/header.html`, `overlay/css/open-circuits.css:694–715`

---

**Bug B — `aria-expanded="true"` hardcoded in header template**
Severity: Low

The toggle button always starts with `aria-expanded="true"` even though on mobile the sidebar
starts closed. This creates a brief ARIA mismatch before JS corrects it.

Fix: change the initial value to `aria-expanded="false"` in the template. JS sets it
correctly on `DOMContentLoaded` for all viewport sizes.

Files: `overlay/templates/header.html:5`

---

**Bug C — `<p>` margins on `.oc-site-title` disrupt header alignment**
Severity: Low–Medium

The site title is a `<p>` tag, and the global `p { margin: 0.75em 0 }` rule applies. Inside
the `display: flex` header this adds unwanted vertical margin.

Fix: add `margin: 0` to `.oc-site-title` in CSS.

Files: `overlay/css/open-circuits.css` (`.oc-site-title` rule)

---

**Bug D — Body not centered on wide screens when sidebar is open**
Severity: Low

`body { max-width: 920px }` has no `margin: 0 auto` when the sidebar is open. Content hugs
the left edge on screens wider than 920px; `margin: 0 auto` only applies via
`body.sidebar-closed`.

Fix: remove `max-width` from body and instead apply it to a wrapper, or rethink the layout so
the body is always centered and the sidebar offsets it via padding rather than asymmetric
margin.

Files: `overlay/css/open-circuits.css:154–174`

---

## Phase 4: Navigation UX

Two issues in `overlay/js/navigation.js`. No CSS changes needed for bug A; bug B is JS-only.

**Bug A — No active-volume indicator in header navigation**
Severity: Low–Medium

All six volume links (`DC | AC | Semi | Digital | Ref | Exper`) are styled identically
regardless of which volume the reader is in. There is no current-page affordance.

Fix: in `navigation.js`, after the DOM is ready, compare the current `window.location.pathname`
against each volume prefix and add an `is-active` class to the matching `<a>` in `.oc-vol-nav`.
Add a corresponding CSS rule for `.oc-vol-nav a.is-active`.

Files: `overlay/js/navigation.js`, `overlay/css/open-circuits.css:444–476`

---

**Bug B — First chapter shows a redundant "Prev" button**
Severity: Low

Kuphaldt's chapter 1 pages link their "previous" image to `index.html` (the volume TOC), the
same destination as the "Contents" link. `navigation.js` picks this up as
`nav.prev = 'index.html'`, so the sidebar renders both "Contents" and "← Prev" pointing to
the same page.

Fix: in `extractChapterNav()`, after resolving `nav.prev`, check whether it equals `nav.index`
and if so set `nav.prev = null` to suppress the redundant button.

Files: `overlay/js/navigation.js:20–35`

---

## Phase 5: ZIM release pipeline

**Bug — ZIM artifact is never attached to releases**
Severity: High — Kiwix/Hearth integration is broken for every release.

`zimwriterfs` is not available in `ubuntu-latest` and is not in the default apt repositories.
The install step in `release.yml` silently falls through, so the ZIM is never built:

```yaml
sudo apt-get install -y zimwriterfs 2>/dev/null || echo "zimwriterfs not available"
```

The v1.0.0 release confirms this: only the HTML tarball is attached; no `.zim` artifact.

Fix options (pick one):
1. Add a third-party apt source or snap for `zimwriterfs` in CI.
2. Switch to the `openzim/zimit` Docker image which bundles `zimwriterfs`.
3. Build ZIM in a separate workflow job using `ghcr.io/openzim/zimwriterfs` container action.

Files: `.github/workflows/release.yml`, `build/build_zim.py`

---

## Phase 6: Browser testing

**Task — Verify navigation sidebar in a real browser**
Severity: Unknown

Phase 9 of the original project plan deferred browser testing. The following have never been
verified against real Kuphaldt HTML:

- TOC builder (`buildTocItems`) — does it correctly find `<a name="...">` anchors inside `<h2>` tags?
- Scroll-spy (`setupScrollSpy`) — does it highlight the right section as the reader scrolls?
- Prev/next extraction (`extractChapterNav`) — does it correctly identify `previous.jpg` / `next.jpg` links?
- Mobile sidebar open/close toggle — does it animate correctly after Phase 3 fixes?
- Bottom chapter nav — does it appear in the right place relative to the footer?

Method: run `make build` locally, open `output/html/DC/DC_2.html` in a browser, and exercise
each of the above. DC_2.html is the best test case — it has both a prev and a next link.

Files: `overlay/js/navigation.js`
