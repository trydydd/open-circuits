# Attribution — Open Circuits

## Original Work

**Title:** Lessons in Electric Circuits
**Author:** Tony R. Kuphaldt
**Source:** https://www.ibiblio.org/kuphaldt/electricCircuits/
**License:** Design Science License (DSL)

This project is based on *Lessons in Electric Circuits*, a six-volume
electronics textbook written by Tony R. Kuphaldt and published freely at
`ibiblio.org`. The text covers DC circuits, AC circuits, semiconductors,
digital logic, reference tables, and hands-on experiments.

The original work is copyright Tony R. Kuphaldt and is published under the
Design Science License. The full license text is included in this repository
as `LICENSE-DSL.txt`.

---

## Derivative Work

**Title:** Open Circuits — A Portable Electronics Reference
**Repository:** https://github.com/trydydd/open-circuits
**License:** Design Science License (DSL) (same as original, as required)

This derivative work was created by the **Hearth project** and consists of:

1. **Format conversion** — The pre-built HTML bundle from ibiblio is
   downloaded and processed, with a CSS overlay and navigation elements
   injected into each page to improve readability and usability.

2. **CSS overlay** (`overlay/css/open-circuits.css`) — A modern stylesheet
   improving readability (responsive layout, better typography) without
   altering the substantive content of the original text.

3. **Navigation templates** (`overlay/templates/header.html`,
   `overlay/templates/footer.html`) — Header and footer injected into every
   page providing inter-volume navigation and the required attribution notice.

4. **Build tooling** (`build/`, `overlay/inject-overlay.sh`) — Shell scripts
   to download, process, and package the content into deployable formats
   (HTML site, release tarball, ZIM file for Kiwix).

5. **ZIM packaging** — Metadata and scripts to build a `.zim` file suitable
   for distribution via Kiwix, making the text available offline worldwide.

The substantive text (words, diagrams, equations, circuit schematics) is
unchanged from Kuphaldt's original. Only presentation and navigation have
been modified.

---

## Modification Log

| Date | Modifier | Description |
|------|----------|-------------|
| 2026 | Hearth project | Initial conversion: CSS overlay, navigation injection, ZIM packaging |

---

## DSL Section 4 Compliance

This derivative work satisfies the requirements of Section 4 of the Design
Science License:

- **New name:** "Open Circuits — A Portable Electronics Reference" is clearly
  distinct from "Lessons in Electric Circuits" and cannot be confused with
  the original.

- **Authorship credit:** The original text is attributed to Tony R. Kuphaldt
  throughout. Modifications are attributed to the Hearth project.

- **Modification notice:** This file (ATTRIBUTION.md) and the footer on every
  output page describe the nature and date of modifications.

- **Same license:** This derivative work is published under the Design Science
  License, the same license as the original.

- **Source availability:** The GitHub repository contains all source files
  (scripts, templates, CSS) needed to reproduce the output. The upstream
  HTML source is downloaded at build time from the publicly accessible URL
  at ibiblio.org.

---

## Required Notice

The following notice appears on every page of the built site:

> Based on "Lessons in Electric Circuits" by Tony R. Kuphaldt.
> Converted and restyled by the Hearth project, 2026.
> Published under the Design Science License.
