# Conversion Notes

Technical decisions, upstream HTML quirks, and the forward path toward a deeper conversion.

---

## Why Option A (Pre-Built HTML) Was Chosen

The spec considered three conversion strategies:

| Option | Description |
|--------|-------------|
| **A** | Download Kuphaldt's pre-built HTML bundle from ibiblio, inject a CSS overlay |
| **B** | Use the SubML source + sed/Make toolchain to build HTML from scratch, then restyle |
| **C** | Convert SubML → Markdown, build with mdBook or similar static site generator |

**Option A was chosen for the initial release** for the following reasons:

1. **Zero conversion risk.** The pre-built HTML at ibiblio is Kuphaldt's own output. Using it as-is means no lossy conversion step, no risk of dropped content or mis-rendered equations, and no need to understand SubML.

2. **Immediate deliverable.** The first priority was a working, deployable site. Option A produces one in a single build step.

3. **The text is frozen.** Kuphaldt stepped back as primary author around 2004. Only minor corrections have been made since. There is no continuous upstream to track, so the cost of Option A's "snapshot and ship" approach is low.

4. **CC BY 4.0 compliance is simpler.** Using the pre-built HTML, we only need to inject attribution — we do not need to re-implement or verify the rendering of the original content.

Option B remains the recommended long-term direction (see below). Option C has the highest long-term upside but the highest conversion risk due to SubML features (SPICE output, schematic images) that do not map cleanly to Markdown.

---

## Upstream HTML Structure

The tarball (`liechtml.tar.gz`, ~36 MB) extracts to a flat tree of volume subdirectories:

```
upstream/html/
├── index.htm          # Root index (lists all volumes)
├── DC/
│   ├── DC_1.html      # Chapter 1 — Basic Concepts of Electricity
│   ├── DC_2.html      # Chapter 2 — Ohm's Law
│   └── ...
├── AC/
│   ├── AC_1.html
│   └── ...
├── Semi/
│   ├── SEMI_1.html
│   └── ...
├── Digital/
│   ├── DIGI_1.html
│   └── ...
├── Ref/
│   ├── REF_1.html
│   └── ...
└── Exper/
    ├── EXPER_1.html
    └── ...
```

**File naming convention:** `{VOL}_{N}.html` where `VOL` is the volume prefix and `N` is the chapter number. The prefixes are: `DC`, `AC`, `SEMI`, `DIGI`, `REF`, `EXPER`.

**Root index:** The top-level file is `index.htm` (not `.html`). `inject_overlay.py` normalises `.htm` → `.html` in the output, so the built site serves `index.html`.

**Images:** Schematic and diagram images are in JPEG format, embedded relative to each chapter file. They are copied verbatim into the output — no recompression or conversion is done.

---

## Known Quirks That Affect Injection

### `<head>` structure

Kuphaldt's pages use a minimal `<head>`. Most pages have a well-formed `</head>` tag, allowing the CSS `<link>` to be injected cleanly before it. A small number of pages lack a `</head>` — `inject_overlay.py` handles this by prepending the `<link>` to the file as a fallback.

### `<body>` attributes

Several pages include `bgcolor`, `text`, `link`, and `vlink` attributes on the `<body>` tag (e.g. `<body bgcolor="#ffffff">`). These are early-2000s era inline color declarations. The CSS overlay overrides them via `body { background: ...; color: ...; }` declarations, but they remain in the source HTML. They do not affect injection.

### Inline styles

Many pages use `<font>` tags, `<center>`, and `align=` attributes that are obsolete in modern HTML. The overlay CSS resets the most visually disruptive of these. A future Option B conversion would eliminate them.

### Internal navigation links

The original HTML includes per-chapter "previous / next" links and a table of contents at the top of each file. These are left intact. The injected header adds inter-volume navigation on top of the existing per-volume navigation.

### Depth-relative paths

Pages in volume subdirectories (e.g. `DC/DC_1.html`) are one level deep; the root `index.html` is at depth 0. The `inject_overlay.py` script resolves all injected paths (CSS href, header nav links, footer links) relative to each file's depth using `../` prefixes. The template system uses `{{PLACEHOLDER}}` tokens for this — see `overlay/inject_overlay.py:resolve_paths()`.

### Encoding

All pages are Latin-1 / ISO-8859-1. `inject_overlay.py` reads them with `errors="replace"` to handle any stray bytes and writes the output as UTF-8. This is safe because Kuphaldt's text is plain ASCII; no characters outside the ASCII range appear in the body text.

---

## Future Path: Option B (SubML → Modern HTML)

If a deeper conversion is ever desired, the path is:

1. **Download the full source tarball** (`liecsrc.tar`, ~100 MB from ibiblio) instead of `liechtml.tar.gz`. This contains the SubML `.sml` files and the `Makefile`/`sed` toolchain.

2. **Understand SubML.** It is a custom SGML-like format with a sed-based converter. The converter is documented in `src/convert.sed` in the tarball. Key constructs: `<chapter>`, `<section>`, `<subsection>`, `<image>`, `<spice>`, `<index>`. The `<spice>` construct embeds SPICE netlists — these render as preformatted text in the HTML output.

3. **Run the upstream toolchain** to produce HTML, then replace the injection step with a full restyle pipeline.

4. **Or, convert SubML to Markdown/HTML directly** using a custom parser (Python or Go). The sed toolchain is a reference for the tag semantics. A custom parser would have more control over the output structure and could add semantic elements (`<nav>`, `<article>`, `<figure>`) that the sed toolchain does not.

**Key risk:** The schematic images are pre-rendered JPEGs in the source tarball, not vector sources. Any Option B conversion still ships these raster images. Replacing them with SVG schematics would require a separate tooling effort (e.g. processing the SPICE netlists through a schematic renderer).

The `build/download_source.py` script's `SOURCE_URL` constant would need to be updated to point at `liecsrc.tar` for an Option B build.
