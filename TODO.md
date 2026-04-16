# Open Circuits — Bug Fix Phases

Audited from static code analysis and inspection of the v1.0.0 release tarball.
Live site (`https://trydydd.github.io/open-circuits/`) was not accessible during audit (403).

Phases are ordered by dependency. Phases marked **parallel-safe** can be worked on
simultaneously on separate branches with no expected merge conflicts.

---

## Phase 1: Broken links ✓ done
**Files:** `overlay/inject_overlay.py`

"Master index" links on every volume page pointed to `../index.htm` instead of `../index.html`
because the build renamed the file but never rewrote internal links referencing it. Fixed by
adding a `re.sub` pass in `inject_file()` that rewrites local `.htm` hrefs/srcs to `.html`.

---

## Phase 2: CSS fixes — parallel-safe
**Files:** `overlay/css/open-circuits.css` only

All CSS bugs in one pass. No JS or template changes.

**Bug A — OKLCH palette has no fallback colors** *(severity: medium)*

Every color token uses `oklch()` with no `rgb()` fallback. `oklch()` requires Chrome 111+,
Firefox 113+, or Safari 15.4+. Older browsers (including many cheap Android WebViews) silently
ignore all `oklch()` values and fall back to UA defaults, stripping the entire color theme.

Fix: add `rgb()` fallback declarations immediately before each `oklch()` value in the `:root`
and dark-mode blocks. (lines 53–128)

---

**Bug B — CSS Relative Color Syntax has limited browser support** *(severity: low)*

```css
.oc-bottomnav__index {
  border-color: oklch(from var(--oc-accent) l c h / 0.35) !important;
}
```

Requires Chrome 119+, Firefox 128+, or Safari 16.4+. On older browsers the border renders at
full opacity.

Fix: replace with a static `oklch()` (or CSS variable) that approximates 35% opacity, removing
the relative-color-syntax dependency. (line 654)

---

**Bug C — `color-mix(in oklch, ...)` table striping has limited support** *(severity: low)*

```css
tr:nth-child(even) td {
  background: color-mix(in oklch, var(--oc-surface) 60%, var(--oc-bg) 40%);
}
```

Requires Chrome 111+, Firefox 113+, or Safari 16.2+. On older browsers even rows lose their
stripe.

Fix: add a static fallback color on the line above `color-mix()`. (line 311)

---

**Bug D — `<p>` margins on `.oc-site-title` disrupt header alignment** *(severity: low–medium)*

The site title is a `<p>` tag; global `p { margin: 0.75em 0 }` applies. Inside the flex header
this adds unwanted vertical margin.

Fix: add `margin: 0` to the `.oc-site-title` rule.

---

**Bug E — Body not centered on wide screens when sidebar is open** *(severity: low)*

`body { max-width: 920px }` has no `margin: 0 auto` when the sidebar is open. `margin: 0 auto`
only applies via `body.sidebar-closed`, so on wide screens the content hugs the left.

Fix: adjust the body/sidebar-closed rules so the body is always centered and the sidebar
indents it via padding rather than asymmetric margin. (lines 154–174)

---

**Bug F — No active-volume indicator in header navigation** *(severity: low–medium)*

All six volume links are styled identically regardless of which volume the reader is in. Needs
a `.oc-vol-nav a.is-active` CSS rule (the JS side is in Phase 3).

Fix: add `.oc-vol-nav a.is-active` styles. (lines 444–476)

---

## Phase 3: JS + template fixes — parallel-safe
**Files:** `overlay/js/navigation.js`, `overlay/templates/header.html`

No CSS changes — all CSS work is in Phase 2.

**Bug A — Mobile sidebar flashes open before JS loads** *(severity: medium)*

The header template emits `<body>` with no `sidebar-closed` class. The CSS rule
`body:not(.sidebar-closed) .oc-sidebar { transform: translateX(0) }` has higher specificity
than the mobile-default `transform: translateX(-100%)`, so the sidebar is visible until JS
runs.

Fix: add `class="sidebar-closed"` to the `<body>` tag in `header.html`. The existing
`setOpen(isDesktop())` call in JS already removes it on desktop and leaves it on mobile —
no JS logic changes needed.

Files: `overlay/templates/header.html`

---

**Bug B — `aria-expanded="true"` hardcoded in header template** *(severity: low)*

The toggle starts with `aria-expanded="true"` even though on mobile the sidebar starts closed.

Fix: change to `aria-expanded="false"`. JS sets it correctly in `setupToggle()` for all sizes.

Files: `overlay/templates/header.html:5`

---

**Bug C — First chapter shows a redundant "Prev" button** *(severity: low)*

Kuphaldt's chapter 1 "previous" image links to `index.html` (the volume TOC), the same
destination as the "Contents" link. `navigation.js` picks this up as `nav.prev = 'index.html'`
and renders a "← Prev" button pointing to the same page as "Contents".

Fix: in `extractChapterNav()`, after resolving `nav.prev`, if it equals `nav.index` set
`nav.prev = null`. (lines 20–35)

Files: `overlay/js/navigation.js`

---

**Bug D — No active-volume indicator (JS side)** *(severity: low–medium)*

Companion to Phase 2 Bug F. The CSS rule exists after Phase 2; this adds the JS that applies
it.

Fix: in `navigation.js` init, compare `window.location.pathname` against each volume prefix
and add `is-active` to the matching `.oc-vol-nav` link.

Files: `overlay/js/navigation.js`

---

## Phase 4: ZIM release pipeline — parallel-safe
**Files:** `.github/workflows/release.yml`, `build/build_zim.py`

Fully independent of all other phases. No HTML, CSS, or JS changes.

**Bug — ZIM artifact never attached to releases** *(severity: high)*

`zimwriterfs` is absent from `ubuntu-latest` and not in the default apt repos. The install
step silently falls through:

```yaml
sudo apt-get install -y zimwriterfs 2>/dev/null || echo "zimwriterfs not available"
```

The v1.0.0 release confirms this: only the HTML tarball is attached; no `.zim` artifact.

Fix options (pick one):
1. Add the OpenZIM PPA or snap to CI before the install step.
2. Run the ZIM build step in a `ghcr.io/openzim/zimwriterfs` container action.
3. Build ZIM as a separate workflow job using the official container.

---

## Phase 5: Browser testing — depends on phases 2 and 3
**Files:** `overlay/js/navigation.js` (fixes from testing go here)

Must run after phases 2 and 3 are merged. Tests the navigation sidebar against real Kuphaldt
HTML in a browser. DC_2.html is the best test case (has both prev and next links).

Checklist:
- [ ] TOC builder finds `<a name="...">` anchors inside `<h2>` tags correctly
- [ ] Scroll-spy highlights the right section as the reader scrolls
- [ ] Prev/next extraction identifies `previous.jpg` / `next.jpg` links correctly
- [ ] Active-volume indicator highlights the correct volume
- [ ] First chapter shows no redundant "Prev" button
- [ ] Mobile sidebar starts closed, opens and closes via toggle
- [ ] Bottom chapter nav appears above the footer
- [ ] Dark mode: all colors render correctly
- [ ] No-JS fallback: page is readable without JavaScript
