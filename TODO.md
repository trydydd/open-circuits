# Open Circuits — Bug List

Audited from static code analysis and inspection of the v1.0.0 release tarball.
Live site (`https://trydydd.github.io/open-circuits/`) was not accessible during audit (403).

---

## Bugs

### 1. ZIM missing from releases
**Severity:** High — Kiwix/Hearth integration is broken for every release.

`zimwriterfs` is not available in the `ubuntu-latest` CI runner and is not in the default apt
repositories. The install step in `release.yml` silently falls through:

```yaml
sudo apt-get install -y zimwriterfs 2>/dev/null || echo "zimwriterfs not available — ZIM will not be attached"
```

The ZIM is never built, so releases ship with only the HTML tarball. The v1.0.0 release confirms
this: only `open-circuits-v1.0.0.tar.gz` is attached; no `.zim` artifact.

**Files:** `.github/workflows/release.yml`, `build/build_zim.py`

---

### 2. Mobile sidebar flash before JS loads
**Severity:** Medium — visible layout glitch on every mobile page load.

The CSS uses `body:not(.sidebar-closed)` to keep the sidebar visible on desktop. On mobile the
base rule hides the sidebar:

```css
@media (max-width: 768px) {
  .oc-sidebar { transform: translateX(-100%); }            /* hides */
  body:not(.sidebar-closed) .oc-sidebar { transform: translateX(0); }  /* overrides — shows */
}
```

Because `body` never has `sidebar-closed` in the initial HTML, the higher-specificity
`:not(.sidebar-closed)` rule wins and the sidebar is visible. JS then adds `sidebar-closed`
(closing it), but until that executes there is a flash of the open sidebar on mobile.

**Files:** `overlay/css/open-circuits.css:694–715`

---

### 3. `<p>` margin on `.oc-site-title` disrupts header layout
**Severity:** Low–Medium — may cause vertical misalignment in the header bar.

The header template wraps the site title in a `<p>` tag:

```html
<p class="oc-site-title"><a href="{{INDEX_PATH}}">Open Circuits</a></p>
```

The global `p { margin: 0.75em 0 }` rule applies. `.oc-site-title` has no `margin: 0` override.
Inside a `display: flex` header this adds top/bottom margin that can nudge the title out of
vertical alignment.

**Files:** `overlay/css/open-circuits.css:207`, `overlay/templates/header.html:14`

---

### 4. No active-volume indicator in header navigation
**Severity:** Low–Medium — hurts orientation on every page.

The volume nav (`DC | AC | Semi | Digital | Ref | Exper`) has no visual distinction for the
current volume. A reader inside the DC volume sees all six links styled identically.

**Files:** `overlay/css/open-circuits.css:444–476`, `overlay/js/navigation.js`

---

### 5. First chapter shows a redundant "Prev" button
**Severity:** Low — confusing UX on chapter 1 of every volume.

Kuphaldt's chapter 1 pages link their "previous" image to `index.html` (the volume TOC).
`navigation.js` picks this up as `nav.prev = 'index.html'`, the same destination as
`nav.index`. The sidebar then renders both a "Contents" link and a "← Prev" button pointing
to the same page.

**Files:** `overlay/js/navigation.js:20–35` (`extractChapterNav`)

---

### 6. CSS Relative Color Syntax has limited browser support
**Severity:** Low — cosmetic degradation on some mobile browsers.

```css
.oc-bottomnav__index {
  border-color: oklch(from var(--oc-accent) l c h / 0.35) !important;
}
```

CSS Relative Color Syntax requires Chrome 119+, Firefox 128+, or Safari 16.4+. On older
browsers the declaration is ignored and the border renders at full opacity.

**Files:** `overlay/css/open-circuits.css:654`

---

### 7. `color-mix(in oklch, ...)` table striping has limited browser support
**Severity:** Low — cosmetic degradation on older Android browsers.

```css
tr:nth-child(even) td {
  background: color-mix(in oklch, var(--oc-surface) 60%, var(--oc-bg) 40%);
}
```

`color-mix()` requires Chrome 111+, Firefox 113+, or Safari 16.2+. On older browsers even
rows lose their alternating background; tables become harder to scan.

**Files:** `overlay/css/open-circuits.css:311`

---

### 8. OKLCH palette has no fallback colors for older browsers
**Severity:** Medium — entire site loses all custom styling on older Android WebView.

Every color token uses `oklch()` with no `rgb()` or `hsl()` fallback. `oklch()` requires
Chrome 111+, Firefox 113+, or Safari 15.4+. Browsers below these versions silently ignore all
`oklch()` values and fall back to browser defaults, rendering the site without the overlay
color theme.

Given the project goal ("readable on a €30 Android phone"), this is a meaningful risk.

**Files:** `overlay/css/open-circuits.css:53–128`

---

### 9. Body not centered on wide screens when sidebar is open
**Severity:** Low — layout looks off on large monitors.

```css
body {
  max-width: 920px;
  padding-left: calc(var(--oc-sidebar-w) + var(--space-xl));  /* 304px */
  /* no margin: auto */
}
body.sidebar-closed {
  margin: 0 auto;  /* only centered when sidebar is closed */
}
```

When the sidebar is open, the body hugs the left edge. On screens wider than 920px, there is
empty space on the right that is not mirrored on the left, making the layout asymmetric.

**Files:** `overlay/css/open-circuits.css:154–174`

---

### 10. `aria-expanded="true"` hardcoded in header template
**Severity:** Low — brief ARIA mismatch on mobile page load.

```html
<button id="oc-nav-toggle" aria-expanded="true" ...>
```

On mobile, `navigation.js` immediately sets `aria-expanded="false"` when closing the sidebar.
Until JS runs, screen readers and assistive technology see `aria-expanded="true"` while the
sidebar is visually closed (bug 2 means it is actually open briefly, so this partially cancels
out — but the root cause of both is the same missing initial `sidebar-closed` class).

**Files:** `overlay/templates/header.html:5`

---

### 11. Navigation sidebar has never been tested in a browser
**Severity:** Unknown — functional correctness unverified.

Phase 9 of the original project plan explicitly deferred browser testing. The sidebar TOC
builder, scroll-spy, and prev/next link extraction have not been verified against real Kuphaldt
HTML in any browser. Bugs 4 and 5 above were found without running the code.

**Files:** `overlay/js/navigation.js`
