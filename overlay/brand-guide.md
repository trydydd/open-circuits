# Open Circuits — Brand Style Guide

---

## Logo

**File:** `overlay/logo.svg`

The mark combines an open-switch arm with a PCB arc and two annular-ring via pads — a schematic open-circuit symbol rendered in PCB aesthetics. Dark charcoal ground (`#26211D`), copper elements (`#935F16`). No gradients, no drop shadows, no rounded blobs.

Elements:
- A 300° arc (gap at 3 o'clock) suggesting the circuit loop
- A switch arm extending from the lower terminal — the open/disconnected state
- Two PCB via pads (copper annular ring + dark drill hole) at the terminals
- A centre node dot

**Usage**
| Context | Min size | Clear space |
|---|---|---|
| Header icon | 24 × 24 px | 4 px on all sides |
| Favicon | 16 × 16 px (downscale from 48 px source) | — |
| Print / documents | 12 mm | 3 mm on all sides |

**Don'ts**
- Do not recolour the mark (no brand colours other than copper on dark, or copper on cream for light backgrounds)
- Do not add a drop shadow or glow
- Do not distort the aspect ratio
- Do not place on a busy or mid-tone background without a solid pad

---

## Colour Palette

All tokens are defined in `overlay/css/open-circuits.css` (`:root` block). `rgb()` values are the canonical fallback; `oklch()` values are used on modern browsers via `@supports`.

### Light theme (default)

| Token | Role | RGB | OKLCH |
|---|---|---|---|
| `--oc-bg` | Page background | `rgb(246 243 235)` | `oklch(96.5% 0.010 82)` |
| `--oc-surface` | Sidebar, cards | `rgb(240 236 229)` | `oklch(93.5% 0.011 82)` |
| `--oc-text` | Body text | `rgb(40 36 32)` | `oklch(20% 0.012 75)` |
| `--oc-text-2` | Secondary text | `rgb(95 90 86)` | `oklch(44% 0.010 75)` |
| `--oc-text-3` | Captions, labels | `rgb(132 128 124)` | `oklch(58% 0.008 75)` |
| `--oc-accent` | Copper accent | `rgb(147 95 22)` | `oklch(55% 0.130 60)` |
| `--oc-accent-dim` | Pressed/hover accent | `rgb(120 74 8)` | `oklch(48% 0.140 58)` |
| `--oc-accent-bg` | Tinted accent area | `rgb(235 225 204)` | `oklch(91% 0.038 72)` |
| `--oc-link` | Link text | `rgb(26 76 171)` | `oklch(38% 0.150 258)` |
| `--oc-border` | Subtle dividers | `rgb(218 213 206)` | `oklch(86% 0.011 82)` |
| `--oc-header-bg` | Site header | `rgb(38 33 29)` | `oklch(19% 0.014 75)` |
| `--oc-header-text` | Header text | `rgb(232 228 224)` | `oklch(91% 0.009 80)` |

Dark mode tokens are defined in `@media (prefers-color-scheme: dark)` in the same file.

**Single accent rule:** copper is the only accent colour. Do not introduce a second accent (teal, orange, purple, etc.).

---

## Typography

| Role | Family | Weight | Size |
|---|---|---|---|
| Body text | Vollkorn (serif) | 400 | 1rem / 17–18 px |
| Body emphasis | Vollkorn | 700 | inherit |
| Headings (h1–h3) | Chivo (grotesque) | 700 | 1.5–2.2 rem |
| UI labels, nav | Chivo | 400–500 | 0.8–0.9 rem |
| Code, preformatted | system-ui monospace | 400 | 0.875 rem |

Both fonts ship as WOFF2 in `overlay/fonts/`. They are self-hosted; do not link to Google Fonts or any CDN.

**Type rhythm:** 4 pt base unit (`--space-*` scale in CSS). Line height 1.6 for body, 1.2 for headings.

---

## Tone

**Three words:** tactile · generous · honest

The interface is in service of the text. It does not perform warmth; warmth comes from type, colour temperature, and spacing. The reader is assumed to be smart, working on a real project.

**Write like a well-used repair manual.** Short sentences. No jargon unless the reader already knows it. No marketing copy. No exclamation marks.

**Anti-patterns (from `.impeccable.md`)**
- Glassmorphism, gradient text, blur effects
- Pure white or pure black backgrounds
- Cyan-on-dark "tech" colour schemes
- Premium magazine layouts (too precious, implies cost)
- Institutional portals (grey, cold, grid-heavy)
- AI-generated design clichés (rounded everything, floating cards, status badges)

---

## ZIM / Kiwix assets

| File | Size | Purpose |
|---|---|---|
| `zim-metadata/favicon.png` | 48 × 48 px | Kiwix browser tab icon |
| `zim-metadata/illustration.png` | 315 × 250 px | Kiwix catalog splash |

Both are derived from the SVG mark. If the mark changes, regenerate the PNGs to match.
