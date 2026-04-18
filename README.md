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

- **Python 3.10+** — the only required system dependency
- `zimwriterfs` — optional, required only for ZIM packaging
  (from [openzim/zim-tools](https://github.com/openzim/zim-tools))

All Python dependencies (BeautifulSoup, pytest) are installed in a local
`.venv/` — no system-level packages needed. Built output is self-contained
with no CDN dependencies at runtime.

---

## Quick Start

```bash
# 1. Create the venv and install dependencies
make install

# 2. Download upstream HTML, inject overlay, verify integrity
make build

# 3. Open the result
open output/html/index.html
```

Or step by step:

```bash
make download   # fetch upstream/html/ from ibiblio
make inject     # produce output/html/ with CSS + nav injected
make verify     # confirm no text was changed
```

To re-download the upstream source (e.g. after an upstream update):

```bash
.venv/bin/python build/download_source.py --force
```

To run the test suite:

```bash
make test
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
├── LICENSE.txt              # Creative Commons Attribution-ShareAlike 4.0 (CC BY-SA 4.0)
├── ATTRIBUTION.md           # Credits, modification log, CC BY-SA 4.0 compliance
├── README.md                # This file
├── pyproject.toml           # Project metadata
├── requirements.txt         # Runtime Python dependencies
├── requirements-dev.txt     # Dev/test dependencies
├── Makefile                 # Convenience targets (install, build, test, …)
│
├── upstream/                # Downloaded at build time (not committed)
│   └── UPSTREAM-VERSION.txt # Records snapshot date and source URL
│
├── build/
│   ├── download_source.py        # Fetches HTML bundle from ibiblio
│   ├── verify_content_integrity.py  # Checks output text matches upstream
│   ├── build-html.sh             # (Phase 5) Orchestration — not yet written
│   ├── build-zim.sh              # (Phase 6) ZIM packaging — not yet written
│   └── build-all.sh              # (Phase 5) Full pipeline — not yet written
│
├── overlay/
│   ├── css/open-circuits.css         # Readability CSS overlay
│   ├── js/navigation.js              # Optional sidebar TOC (v1.1)
│   ├── templates/header.html         # Navigation banner, injected at top
│   ├── templates/footer.html         # Attribution notice, injected at bottom
│   └── inject_overlay.py             # Injects header/footer/CSS into HTML
│
├── zim-metadata/            # Metadata for ZIM packaging
├── output/                  # Built artifacts — gitignored
├── tests/
│   ├── conftest.py          # Pytest session fixtures (download + inject)
│   └── test_integration.py  # End-to-end integration tests
├── .github/workflows/       # CI, Pages deployment, release automation
└── docs/                    # Detailed build and integration docs
```

---

## License

The original text is copyright Tony R. Kuphaldt (© 2000–2023) and published
under the **Creative Commons Attribution 4.0 International** license (CC BY 4.0).
This derivative work is published under **Creative Commons Attribution-ShareAlike
4.0 International** (CC BY-SA 4.0).

> Based on "Lessons in Electric Circuits" by Tony R. Kuphaldt.
> Converted and restyled by the Hearth project, 2026.
> Published under CC BY-SA 4.0.

See `LICENSE.txt` for the full license text and `ATTRIBUTION.md` for
complete credits and modification notices.
