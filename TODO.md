# Open Circuits — Project TODO

> Deliverables from `open-circuits-spec.md`, broken into chunks sized for a single Claude Code context window.
> Each phase is a coherent unit of work with a clear definition of done.

---

## Phase 1: Foundation
*Repo scaffolding, legal files, and project documentation stubs.*

- [x] Create directory structure with `.gitkeep` placeholders:
  `upstream/`, `build/`, `overlay/css/`, `overlay/js/`, `overlay/templates/`,
  `zim-metadata/`, `output/`, `.github/workflows/`, `docs/`
- [x] Add `LICENSE.txt` — Creative Commons Attribution 4.0 International (CC BY 4.0)
- [x] Add `ATTRIBUTION.md` — credits Kuphaldt, describes what was modified and when;
  satisfies CC BY 4.0 attribution requirements
- [x] Add `README.md` — project overview, build prerequisites, quick-start instructions,
  license notice
- [x] Add `upstream/UPSTREAM-VERSION.txt` — placeholder noting snapshot date/URL to be
  filled in by `download_source.py`
- [x] Add `output/.gitignore` — ignore all built artifacts under `output/`
- [x] Commit: "chore: scaffold repo structure and legal files"

---

## Phase 2: Download Pipeline
*Script to fetch Kuphaldt's pre-built HTML bundle from ibiblio.*

- [x] Write `build/download_source.py`:
  - Download `liechtml.tar.gz` from `https://www.ibiblio.org/kuphaldt/electricCircuits/`
  - Extract to `upstream/html/`
  - Write snapshot date and source URL to `upstream/UPSTREAM-VERSION.txt`
  - Be idempotent: skip download if `upstream/html/` already populated (with `--force` flag to re-download)
  - Exit non-zero on download failure
- [x] Test locally: run script, verify `upstream/html/` contains volume subdirectories
  (`DC/`, `AC/`, `Semi/`, `Digital/`, `Ref/`, `Exper/`)
- [x] Commit: "feat: add download_source.py"

---

## Phase 3: Overlay Assets
*CSS stylesheet and HTML header/footer templates injected into every page.*

- [x] Write `overlay/css/open-circuits.css`:
  - Improve readability (max-width body, better fonts, line-height) without dramatically
    altering the original appearance
  - Responsive layout (mobile-readable)
  - Style the injected header and footer regions
  - No external URLs — all self-contained (no Google Fonts, no CDN)
- [x] Write `overlay/templates/header.html`:
  - Project name banner: "Open Circuits — A Portable Electronics Reference"
  - Inter-volume navigation links (DC | AC | Semiconductors | Digital | Reference | Experiments)
  - Link back to index
- [x] Write `overlay/templates/footer.html`:
  - Small "License & Attribution" link pointing to `LICENSE.txt` and `ATTRIBUTION.md`
  - No need to repeat the full attribution text on every page (full notice lives on
    the root `index.html` and in `ATTRIBUTION.md`)
- [x] Commit: "feat: add CSS overlay and header/footer templates"

---

## Phase 4: Overlay Injection Script
*Python script that inserts header, footer, and CSS link into every upstream HTML page.*

- [x] Write `overlay/inject_overlay.py`:
  - Takes input dir (built HTML) and output dir as arguments
  - For each `.html` / `.htm` file (`.htm` renamed to `.html` in output):
    - Copy file to output dir (preserving subdirectory structure)
    - Insert `<link rel="stylesheet" href="...open-circuits.css">` in `<head>`
    - Inject `header.html` content after `<body>` tag
    - Inject `footer.html` content before `</body>` tag
    - Copy CSS file and any JS to output alongside HTML
  - Handle both top-level index pages and volume subdirectory pages
    (CSS path must be relative: `../css/` vs `css/` depending on depth)
  - Validate: parse output for any `http://` or `https://` resource URLs not in the
    attribution footer — exit non-zero if external URLs found
- [x] Test on real upstream HTML from `upstream/html/`
- [x] Commit: "feat: add inject_overlay.py"

---

## Phase 5: Build Orchestration
*Scripts that tie the pipeline together and produce the final HTML site.*

- [x] Write `build/build_html.py`:
  - Ensures `upstream/html/` exists (calls `download_source.py` if not)
  - Creates `output/html/` (clean or incremental)
  - Calls `overlay/inject_overlay.py upstream/html/ output/html/`
  - Runs post-build checks:
    - No external URLs in output (validation)
    - Attribution notice present in a sample page
  - Prints summary: page count, any warnings
- [x] Write `build/build_all.py`:
  - Calls `download_source.py` → `build_html.py` → `build_zim.py` in sequence
  - Creates release tarball: `output/open-circuits-$(git describe --tags).tar.gz`
    from `output/html/`
  - Exits non-zero if any step fails
- [x] Commit: "feat: add build_html.py and build_all.py"

---

## Phase 6: ZIM Packaging
*Metadata assets and script to build a `.zim` file for Kiwix.*

- [x] Create `zim-metadata/metadata.yaml`:
  - `title`: "Open Circuits — A Portable Electronics Reference"
  - `description`: one-paragraph summary of Kuphaldt's text and this project
  - `language`: `eng`
  - `creator`: `Tony R. Kuphaldt`
  - `publisher`: `Hearth Project`
  - `date`: current date
  - `tags`: `electronics;reference;education`
- [x] Create `zim-metadata/favicon.png` — 48×48 px icon for Kiwix library
  (can be a simple placeholder; replace before first release)
- [x] Create `zim-metadata/illustration.png` — 315×250 px illustration for Kiwix catalog
  (placeholder acceptable for v1)
- [x] Write `build/build_zim.py`:
  - Checks `zimwriterfs` is available; prints install hint if not
  - Runs `zimwriterfs` with source `output/html/`, metadata from `zim-metadata/`,
    output to `output/open-circuits.zim`
  - Validates: ZIM file exists and is non-zero bytes
- [x] Commit: "feat: add ZIM metadata and build_zim.py"

---

## Phase 7: CI/CD Workflows
*Three GitHub Actions workflows covering CI, Pages deployment, and tagged releases.*

- [x] Write `.github/workflows/build.yml` (runs on every push):
  - Install `zimwriterfs` if available in CI image, or skip ZIM step
  - Run `python build/build_all.py`
  - Verify: no external URLs in `output/html/`
  - Verify: attribution notice present in `output/html/index.html`
  - Upload `output/html/` as a build artifact for inspection
- [x] Write `.github/workflows/pages.yml` (runs on push to `main`):
  - Run `python build/build_html.py`
  - Deploy `output/html/` to GitHub Pages using `actions/deploy-pages`
  - Ensure `output/html/` has a root `index.html` (create one if upstream doesn't)
- [x] Write `.github/workflows/release.yml` (runs on version tag `v*`):
  - Run `python build/build_all.py`
  - Attach `output/open-circuits-*.tar.gz` to GitHub release
  - Attach `output/open-circuits.zim` to GitHub release (if built successfully)
- [x] Commit: "ci: add build, pages, and release workflows"

---

## Phase 8: Documentation
*Detailed docs for contributors and Hearth integration.*

- [x] Write `docs/BUILDING.md`:
  - Prerequisites (`python3`, `make`, `curl`, `zimwriterfs`)
  - Step-by-step local build instructions
  - How to test the output (open in browser, check with `kiwix-serve`)
  - How to add or update the overlay CSS
- [x] Write `docs/CONVERSION-NOTES.md`:
  - Why Option A (pre-built HTML) was chosen over SubML conversion
  - Notes on the upstream HTML structure (volume dirs, file naming conventions)
  - Known quirks of Kuphaldt's HTML that affect injection
  - Future path toward Option B (SubML → modern HTML) if desired
- [x] Write `docs/HEARTH-INTEGRATION.md`:
  - How the Hearth ansible role consumes release artifacts
  - nginx path convention: `/circuits/DC/DC_1.html` etc.
  - ZIM mode: where to place the `.zim` file in Hearth
  - URL stability contract (paths must not change across versions)
  - How `salvage-electronics` links into this content
- [x] Commit: "docs: add BUILDING, CONVERSION-NOTES, and HEARTH-INTEGRATION"

---

## Phase 9: Navigation Enhancement *(v1.1 — defer if time-constrained)*
*Client-side JavaScript sidebar table of contents.*

- [x] Write `overlay/js/navigation.js`:
  - Builds a collapsible sidebar TOC from the current volume's heading structure
  - Adds inter-volume prev/next chapter links at the top and bottom of each page
  - Highlights current section in TOC as the user scrolls
  - No external dependencies — vanilla JS only, fully self-contained
- [x] Update `overlay/templates/header.html` to include sidebar scaffold markup
- [x] Update `overlay/css/open-circuits.css` with sidebar layout styles
- [ ] Test: open a chapter page locally, verify TOC builds correctly
- [ ] Commit: "feat: add navigation sidebar (TOC + inter-volume nav)"

---

## Phase 10: End-to-End Validation & First Release
*Full pipeline smoke test, then tag and push v1.0.0.*

- [x] Run full local build: `python3 build/build_all.py`
- [x] Open `output/html/` in a browser — spot-check all six volumes load correctly
- [x] Verify self-contained: `python3 build/verify_content_integrity.py upstream/html/ output/html/`
  should report no external resource URLs
- [x] Verify attribution present on root index:
  `grep -l 'CC BY 4.0\|Creative Commons' output/html/index.html` should match
- [x] Verify URL path stability: confirm `DC/DC_1.html`, `AC/AC_1.html`, etc. exist
  at the expected paths (fixed: Experiments volume uses `EXP_1.html`, not `EXPER_1.html`)
- [ ] (Optional) Test ZIM: `kiwix-serve output/open-circuits.zim` and browse in browser
- [ ] Push branch, confirm GitHub Actions `build.yml` passes
- [ ] Merge to `main`, confirm `pages.yml` deploys to GitHub Pages
- [ ] Tag `v1.0.0`, confirm `release.yml` attaches tarball and ZIM to release
- [ ] Commit/tag: "release: v1.0.0 — first public release"

---

## Reference

| Upstream source | https://www.ibiblio.org/kuphaldt/electricCircuits/ |
|---|---|
| Pre-built HTML bundle | `liechtml.tar.gz` (~36 MB) |
| License | Creative Commons Attribution 4.0 (CC BY 4.0) |
| Output paths | `DC/DC_N.html`, `AC/AC_N.html`, `Semi/SEMI_N.html`, `Digital/DIGI_N.html` |
| Required notice | See `overlay/templates/footer.html` |
| Spec | `open-circuits-spec.md` |
