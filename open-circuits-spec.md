# Open Circuits — Project Specification

> **A Portable Electronics Reference**
> Based on *Lessons in Electric Circuits* by Tony R. Kuphaldt

## Purpose

This project converts Tony R. Kuphaldt's *Lessons in Electric Circuits* — a
six-volume open-licensed electronics textbook — into modern, portable formats
suitable for offline deployment.

The source text is published under the **Creative Commons Attribution 4.0
International** license (CC BY 4.0) and has been freely available at
`ibiblio.org` since 2000. It covers DC circuits,
AC circuits, semiconductors, digital logic, reference tables, and experiments.
It is comprehensive, well-written, and used in college curricula.

No ZIM file or modern web edition of this text currently exists. This project
creates both, contributing them to the commons.

---

## Context: The Three-Repo Architecture

This repo is one of three that together provide a "learn electronics and
salvage" resource for the **Hearth** offline community hub project:

| Repo | Content | License |
|------|---------|---------|
| **`open-circuits`** (this repo) | Kuphaldt's text converted to modern formats | CC BY 4.0 (same as upstream) |
| **`salvage-electronics`** (separate repo) | Original pathway content: salvage techniques, component testing, donor device guides | CC-BY-SA (our choice — compatible with CC BY 4.0 upstream) |
| **`hearth`** (platform repo) | Consumes release artifacts from both repos above, serves via nginx or Kiwix | MIT |

The `salvage-electronics` pathway links into `open-circuits` for deep theory
references. Both are independently useful and independently deployable.

This spec covers only the `open-circuits` repo.

---

## Source Material

### Location
- **Homepage:** https://www.ibiblio.org/kuphaldt/electricCircuits/
- **HTML bundle:** https://www.ibiblio.org/kuphaldt/electricCircuits/liechtml.tar.gz (~36 MB)
- **Full source (SubML + images):** https://www.ibiblio.org/kuphaldt/electricCircuits/liecsrc.tar (~100 MB)
- **Minimal source:** https://www.ibiblio.org/kuphaldt/electricCircuits/liectiny.tar (~8 MB)

### Volumes

| Volume | Title | Last Major Revision | Minor Revision |
|--------|-------|--------------------:|---------------:|
| I | DC | October 2006 | February 2023 |
| II | AC | July 2007 | November 2021 |
| III | Semiconductors | April 2009 | November 2021 |
| IV | Digital | November 2007 | November 2021 |
| V | Reference | January 2006 | November 2021 |
| VI | Experiments | January 2010 | November 2021 |

### Update Frequency
**The text is effectively frozen.** Kuphaldt stepped back as primary author
in 2004. Since then only minor corrections have been made. We can pin a
snapshot and not worry about upstream drift.

### Source Format
The source is written in **SubML** (Substitutionary Markup Language), a custom
SGML-like markup created by Kuphaldt. It converts to HTML, LaTeX, and DocBook
using `sed` search-and-replace scripts. The conversion toolchain requires only
`sed` and `make` — both standard UNIX utilities.

The pre-built HTML is also available for download and does not require the
SubML toolchain at all.

---

## License Compliance (Creative Commons Attribution 4.0)

The upstream work is published under CC BY 4.0 — a permissive attribution
license with no copyleft/share-alike requirement. Full license text:
https://creativecommons.org/licenses/by/4.0/legalcode

### Requirements for Our Use Case

**We are creating a derivative work** (restyled/reformatted HTML), so the
CC BY 4.0 attribution requirements apply:

1. **Credit the creator.** — Original material is attributed to Tony R.
   Kuphaldt throughout: in ATTRIBUTION.md, the footer of every page, and
   the README.

2. **Include the copyright notice.** — © 2000–2023 Tony R. Kuphaldt is
   preserved and reproduced in ATTRIBUTION.md and LICENSE.txt.

3. **Include the license notice.** — LICENSE.txt in the repo and in every
   built distribution. A "CC BY 4.0" link in the footer of every page.

4. **Indicate changes were made.** — ATTRIBUTION.md and the page footer
   describe the nature of modifications (CSS overlay, navigation injection,
   packaging) and credit the Hearth project.

5. **No new name required.** — CC BY 4.0 does not require renaming
   derivative works. We retain "Open Circuits — A Portable Electronics
   Reference" as a distinct title, but this is not a compliance obligation.

6. **No ShareAlike requirement.** — CC BY 4.0 is not copyleft. Downstream
   users of this project are not obligated to use the same license.

### Compatibility with Companion Repos
CC BY 4.0 imposes no restrictions on what licenses companion repos may use.
The `salvage-electronics` repo (original content, CC-BY-SA) and `hearth`
(MIT) can be bundled alongside this content without license conflict.

### Required Files in Repo
- `LICENSE.txt` — CC BY 4.0 license with copyright notice
- `ATTRIBUTION.md` — Credits Kuphaldt, describes modifications, copyright

### Required Attribution Notice
CC BY 4.0 requires "appropriate credit" in any distribution. The following
satisfies this:

- `ATTRIBUTION.md` present in the repo and distribution (see above)
- `LICENSE.txt` present in the repo and distribution (see above)
- Attribution notice on the root `index.html` of the built site:
  ```
  Based on "Lessons in Electric Circuits" by Tony R. Kuphaldt.
  Converted and restyled by the Hearth project, [year].
  Published under CC BY 4.0.
  ```
- A "CC BY 4.0" link in the footer of every page pointing to `LICENSE.txt`
  and `ATTRIBUTION.md`.

---

## Deliverables

### 1. GitHub Pages Site
A clean, modern, navigable HTML edition of all six volumes, deployed
automatically on push to `main`. This is the publicly accessible online
version anyone can use.

### 2. Release Tarball
A self-contained `.tar.gz` of the built HTML site, attached to GitHub
releases on tagged versions. This is what Hearth's ansible role downloads
and unpacks for offline serving via nginx.

### 3. ZIM File
A `.zim` file built with `zimwriterfs`, also attached to GitHub releases.
This can be served by any Kiwix instance worldwide — not just Hearth. It
should include proper metadata (title, description, language, favicon,
illustration) so it appears correctly in Kiwix library listings.

---

## Approach: Conversion Strategy

### Option A: Verbatim HTML Bundle (Fastest, Simplest)
Take the pre-built HTML from ibiblio, serve as-is with an optional CSS
overlay for minor styling improvements.

- **Pro:** Zero conversion risk, immediate result, trivial build step.
- **Con:** The HTML is early-2000s era — functional but dated. No consistent
  navigation, no search, visually disconnected from companion content.

### Option B: SubML → Modern HTML (Recommended)
Use the existing SubML source and sed/Make toolchain to produce HTML, then
restyle with a modern CSS layer and add navigation.

- **Pro:** Clean, consistent output. Good navigation. Matches the era we
  live in. Can add search, table of contents, inter-volume navigation.
- **Con:** More upfront work. Need to understand SubML toolchain.

### Option C: SubML → Markdown → Static Site Generator
Convert SubML to markdown, then build with mdBook or similar.

- **Pro:** Markdown is the most maintainable long-term format. Easy for
  future contributors. Built-in search with mdBook.
- **Con:** Highest conversion effort. SubML has features (circuit diagrams,
  SPICE output) that may not map cleanly to markdown. Risk of lossy
  conversion.

### Recommended Path
**Start with Option A** to get a working deployment immediately. Then
**iterate toward Option B** by adding a CSS overlay, navigation wrapper,
and search to the existing HTML output. This gives us a working product
at every stage.

If Option C proves tractable after examining the source (the SubML may be
simple enough that sed-to-markdown works cleanly), it's the best long-term
outcome. But don't block the initial release on it.

**Key constraint:** the build must work without network access at runtime.
All assets (fonts, CSS, JS, images) must be self-contained in the output.
No CDN references, no external requests.

---

## Repository Structure

```
open-circuits/
├── LICENSE.txt                     # Creative Commons Attribution 4.0 (CC BY 4.0)
├── ATTRIBUTION.md                  # Credits, modification log
├── README.md                       # Project overview, build instructions
│
├── upstream/                       # Kuphaldt's original source
│   ├── .gitkeep                    # Source downloaded at build time
│   └── UPSTREAM-VERSION.txt        # Pinned version/date of snapshot
│
├── build/
│   ├── download-source.sh          # Fetches source tarball from ibiblio
│   ├── build-html.sh               # Runs SubML→HTML (or just copies pre-built)
│   ├── build-zim.sh                # Packages HTML into .zim with zimwriterfs
│   └── build-all.sh                # Orchestrates full build pipeline
│
├── overlay/                        # Our additions (navigation, styling)
│   ├── css/
│   │   └── open-circuits.css       # Modern stylesheet overlay
│   ├── js/
│   │   └── navigation.js           # TOC sidebar, inter-volume nav (optional)
│   ├── templates/
│   │   ├── header.html             # Injected at top of each page
│   │   └── footer.html             # Attribution notice, nav links
│   └── inject-overlay.sh           # Script to inject overlay into built HTML
│
├── zim-metadata/                   # ZIM packaging metadata
│   ├── favicon.png                 # 48x48 icon for Kiwix library
│   ├── illustration.png            # 315x250 illustration for Kiwix catalog
│   └── metadata.yaml               # Title, description, language, etc.
│
├── output/                         # Built artifacts (gitignored)
│   ├── html/                       # Final HTML site
│   └── open-circuits.zim           # Final ZIM file
│
├── .github/workflows/
│   ├── build.yml                   # CI: build and test on every push
│   ├── pages.yml                   # Deploy HTML to GitHub Pages on main
│   └── release.yml                 # Build + attach tarball + .zim on tag
│
└── docs/                           # Project documentation
    ├── BUILDING.md                 # Detailed build instructions
    ├── CONVERSION-NOTES.md         # Decisions, gotchas, SubML quirks
    └── HEARTH-INTEGRATION.md       # How to deploy on a Hearth box
```

---

## Build Pipeline

### Prerequisites
- `sed`, `make` — for SubML conversion (standard on any Linux/macOS)
- `zimwriterfs` — for ZIM packaging (from `openzim/zim-tools`)
- `curl` or `wget` — for downloading upstream source
- No runtime dependencies in the output (no Node, no Python, no CDN)

### Steps

```
1. download-source.sh
   - Fetch liechtml.tar.gz (pre-built HTML) from ibiblio
   - Extract to upstream/html/
   - Record version/date in UPSTREAM-VERSION.txt

2. build-html.sh
   - Copy upstream/html/ to output/html/
   - Run inject-overlay.sh:
     - Insert header.html at top of each volume page
     - Insert footer.html (attribution) at bottom
     - Link open-circuits.css in each page's <head>
     - Optionally add navigation.js for sidebar TOC
   - Validate: no external URLs in output (grep check)

3. build-zim.sh
   - Run zimwriterfs with:
     - Source: output/html/
     - Metadata from zim-metadata/
     - Output: output/open-circuits.zim
   - Validate: zim file opens in kiwix-serve

4. build-all.sh
   - Runs steps 1-3 in sequence
   - Creates output/open-circuits-vX.Y.Z.tar.gz from output/html/
```

### CI Workflows

**build.yml** (every push):
- Run build-all.sh
- Verify no external URLs in output
- Verify attribution notice present on sample pages
- Verify ZIM file is valid (if zimwriterfs available in CI)

**pages.yml** (push to main):
- Run build-html.sh
- Deploy output/html/ to GitHub Pages

**release.yml** (tagged push):
- Run build-all.sh
- Attach output/open-circuits-vX.Y.Z.tar.gz to release
- Attach output/open-circuits.zim to release

---

## Hearth Integration

This section documents how the Hearth platform consumes this project's
artifacts. Implementation happens in the `hearth` repo, not here.

### Planned Integration
An ansible role in hearth downloads a pinned release from this repo and
serves it via nginx. The configuration in `hearth.yaml` would look like:

```yaml
services:
  open_circuits:
    enabled: true
    version: "v1.0.0"      # Pinned release tag
    mode: static            # 'static' for nginx, 'kiwix' for ZIM
```

### nginx Path
Content served at `/circuits/` (or similar), following the same pattern as
hearth's chat, jukebox, and admin frontends.

### ZIM Mode (Alternative)
The `.zim` file is placed in `/srv/hearth/kiwix/` alongside Wikipedia and
other ZIM content, served by the existing Kiwix infrastructure.

### URL Structure
For the `salvage-electronics` pathway to link into this content, URLs must
be predictable. The structure follows Kuphaldt's original chapter naming:

```
/circuits/DC/DC_1.html     — Chapter 1 of Volume I (DC)
/circuits/AC/AC_3.html     — Chapter 3 of Volume II (AC)
/circuits/Semi/SEMI_4.html — Chapter 4 of Volume III (Semiconductors)
```

These paths must remain stable across versions.

---

## Content Overview (What's In Kuphaldt's Text)

For reference when building navigation and linking from `salvage-electronics`:

### Volume I — DC
1. Basic Concepts of Electricity
2. Ohm's Law
3. Electrical Safety
4. Scientific Notation and Metric Prefixes
5. Series and Parallel Circuits
6. Divider Circuits and Kirchhoff's Laws
7. Series-Parallel Combination Circuits
8. DC Metering Circuits
9. Electrical Instrumentation Signals
10. DC Network Analysis
11. Batteries and Power Systems
12. Physics of Conductors and Insulators
13. Capacitors
14. Magnetism and Electromagnetism
15. Inductors

### Volume II — AC
1. Basic AC Theory
2. Complex Numbers
3. Reactance and Impedance — Inductive/Capacitive
4. Series/Parallel R, L, and C
5. Resonance
6. Mixed-Frequency AC Signals
7. Filters
8. Transformers
9. Polyphase AC Circuits
10. Power Factor
11. AC Metering Circuits
12. AC Motors

### Volume III — Semiconductors
1. Amplifiers and Active Devices
2. Solid-state Device Theory
3. Diodes and Rectifiers
4. Bipolar Junction Transistors
5. Junction Field-Effect Transistors
6. Insulated-Gate Field-Effect Transistors (MOSFETs)
7. Thyristors
8. Operational Amplifiers
9. Practical Analog Semiconductor Circuits
10. Active Filters
11. DC Motor Drives
12. Electron Tubes (Vacuum Tubes)

### Volume IV — Digital
1. Numeration Systems
2. Binary Arithmetic
3. Logic Gates
4. Switches and Boolean Algebra
5. Electromechanical Relays
6. Ladder Logic
7. Boolean Algebra
8. Karnaugh Mapping
9. Combinational Logic Functions
10. Multivibrators
11. Counters
12. Shift Registers
13. Digital-Analog Conversion
14. Digital Communication
15. Digital Storage (Memory)
16. Principles of Digital Computing

### Volume V — Reference
- Useful equations and conversion factors
- Color codes
- Conductor and insulator tables
- Algebra, trig reference
- Circuit equations

### Volume VI — Experiments
- Hands-on lab exercises corresponding to theory chapters
- Uses common, inexpensive components
- Particularly relevant for salvage-electronics crossover content

---

## Design Decisions Log

| Decision | Rationale |
|----------|-----------|
| Separate repo from salvage-electronics | Clean separation — independently useful and deployable |
| Separate repo from hearth | Independently useful; deployable on GitHub Pages for the world |
| Start with pre-built HTML, not SubML conversion | Lower risk, faster first release; iterate toward deeper conversion |
| Pin upstream snapshot, don't track | Text is frozen since ~2010; no upstream to track |
| Self-contained output (no CDN) | Hard requirement for offline/Hearth deployment |
| ZIM output as a deliverable | No existing ZIM for this text; contribution to global Kiwix commons |
| CSS overlay rather than full retheme | Minimal modification, clear indication of changes per CC BY 4.0; still improves UX |
| Stable URL paths matching original structure | Enables reliable deep linking from salvage-electronics pathway |

---

## Open Questions

1. **Project name confirmed?** Spec assumes "Open Circuits — A Portable
   Electronics Reference" with repo name `open-circuits`. Update if the
   final name differs.

2. **CSS overlay scope:** How much restyling? Options range from "just add a
   nav header and attribution footer" to "full responsive redesign." Start
   minimal, iterate.

3. **Search:** mdBook-style client-side search would be valuable but adds
   JS complexity. Defer to v2, or include if straightforward to add to
   the existing HTML structure?

4. **Volume VI (Experiments) cross-linking:** This volume's lab exercises
   overlap significantly with salvage-electronics content. Plan the
   cross-reference strategy before writing pathway content that covers
   the same ground.

5. **Image optimization:** Kuphaldt's images are old JPEG exports. Worth
   a batch optimization pass (recompress, convert schematics to SVG) or
   ship as-is? Probably ship as-is for v1, optimize later.

---

## Getting Started (For Claude Code)

1. Create the repo structure above.
2. Write the README, LICENSE.txt (CC BY 4.0), and ATTRIBUTION.md.
3. Write `download-source.sh` — fetch and extract the pre-built HTML bundle.
4. Write `inject-overlay.sh` — add header, footer, and CSS to each page.
5. Create a minimal `open-circuits.css` that improves readability without
   dramatically altering the original appearance.
6. Write the GitHub Actions workflows.
7. Test: build locally, verify output is self-contained, verify attribution
   is present.
8. Deploy to GitHub Pages.
9. Add ZIM build step (may need zimwriterfs installed in CI).
