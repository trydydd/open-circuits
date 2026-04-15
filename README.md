# Open Circuits — A Portable Electronics Reference

A modern, portable edition of Tony R. Kuphaldt's *Lessons in Electric Circuits* —
a six-volume open-licensed electronics textbook covering DC, AC, semiconductors,
digital logic, reference tables, and hands-on experiments.

This project wraps the pre-built HTML from ibiblio with a CSS overlay and navigation
elements, then packages it as a static HTML site and a ZIM file for offline use
with Kiwix.

---

## Volumes

| Volume | Title |
|--------|-------|
| I | DC Circuits |
| II | AC Circuits |
| III | Semiconductors |
| IV | Digital |
| V | Reference |
| VI | Experiments |

---

## Build Prerequisites

- `curl` or `wget` — to download the upstream HTML bundle
- `sed` — standard UNIX text processing (used by inject-overlay.sh)
- `bash` — version 4 or later
- `zimwriterfs` — optional, required only for ZIM packaging
  (from [openzim/zim-tools](https://github.com/openzim/zim-tools))

All build output is self-contained — no Node.js, no Python, no CDN dependencies
at runtime.

---

## Quick Start

```bash
# 1. Download and extract the upstream HTML
bash build/download-source.sh

# 2. Build the HTML site with CSS overlay and navigation
bash build/build-html.sh

# 3. (Optional) Build a ZIM file for Kiwix
bash build/build-zim.sh

# 4. Or run the full pipeline
bash build/build-all.sh
```

Output is written to `output/html/`. Open `output/html/index.html` in a
browser to view the result.

To re-download the upstream source (e.g. after an upstream update):

```bash
bash build/download-source.sh --force
```

---

## URL Structure

Pages follow Kuphaldt's original chapter-file naming, prefixed by volume
directory. These paths are stable across versions:

```
DC/DC_1.html       — Chapter 1, Volume I (DC)
AC/AC_3.html       — Chapter 3, Volume II (AC)
Semi/SEMI_4.html   — Chapter 4, Volume III (Semiconductors)
Digital/DIGI_1.html — Chapter 1, Volume IV (Digital)
Ref/REF_1.html     — Volume V (Reference)
Exper/EXPER_1.html — Volume VI (Experiments)
```

---

## Repository Structure

```
open-circuits/
├── LICENSE-DSL.txt          # Full Design Science License text
├── ATTRIBUTION.md           # Credits, modification log, DSL compliance
├── README.md                # This file
│
├── upstream/                # Downloaded at build time (not committed)
│   └── UPSTREAM-VERSION.txt # Records snapshot date and source URL
│
├── build/
│   ├── download-source.sh   # Fetches HTML bundle from ibiblio
│   ├── build-html.sh        # Injects overlay, produces output/html/
│   ├── build-zim.sh         # Packages into .zim for Kiwix
│   └── build-all.sh         # Full pipeline + release tarball
│
├── overlay/
│   ├── css/open-circuits.css         # Readability CSS overlay
│   ├── js/navigation.js              # Optional sidebar TOC (v1.1)
│   ├── templates/header.html         # Navigation banner, injected at top
│   ├── templates/footer.html         # Attribution notice, injected at bottom
│   └── inject-overlay.sh             # Injects header/footer/CSS into HTML
│
├── zim-metadata/            # Metadata for ZIM packaging
├── output/                  # Built artifacts — gitignored
├── .github/workflows/       # CI, Pages deployment, release automation
└── docs/                    # Detailed build and integration docs
```

---

## License

This project is a derivative work published under the **Design Science License**
(DSL), the same license as the original.

> Based on "Lessons in Electric Circuits" by Tony R. Kuphaldt.
> Converted and restyled by the Hearth project, 2026.
> Published under the Design Science License.

See `LICENSE-DSL.txt` for the full license text and `ATTRIBUTION.md` for
complete credits and modification notices.

The original text is copyright Tony R. Kuphaldt.
Modifications (CSS, navigation, build tooling) are copyright the Hearth project.
