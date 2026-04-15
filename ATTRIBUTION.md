# Attribution — Open Circuits

## Original Work

**Title:** Lessons in Electric Circuits
**Author:** Tony R. Kuphaldt
**Source:** https://www.ibiblio.org/kuphaldt/electricCircuits/
**License:** Creative Commons Attribution 4.0 International (CC BY 4.0)
**Copyright:** Copyright (C) 2000–2023 Tony R. Kuphaldt

This project is based on *Lessons in Electric Circuits*, a six-volume
electronics textbook written by Tony R. Kuphaldt and published freely at
`ibiblio.org`. The text covers DC circuits, AC circuits, semiconductors,
digital logic, reference tables, and hands-on experiments.

---

## Derivative Work

**Title:** Open Circuits — A Portable Electronics Reference
**Repository:** https://github.com/trydydd/open-circuits
**License:** Creative Commons Attribution 4.0 International (CC BY 4.0)

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

## CC BY 4.0 Compliance

This derivative work satisfies the requirements of the Creative Commons
Attribution 4.0 International License:

- **Credit the creator:** The original text is attributed to Tony R. Kuphaldt
  throughout — in this file, the footer of every output page, and the README.

- **Copyright notice:** Copyright (C) 2000–2023 Tony R. Kuphaldt is preserved
  and reproduced here.

- **License notice:** The full CC BY 4.0 license is included in this
  repository as `LICENSE.txt` and linked from every page footer.

- **Indication of changes:** This file (ATTRIBUTION.md) and the footer on
  every output page describe the nature and date of modifications made by
  the Hearth project. The substantive text is unchanged.

- **No ShareAlike requirement:** CC BY 4.0 does not require derivative works
  to use the same license. This project is published under CC BY 4.0 by
  choice, in keeping with the spirit of the original.

---

## Required Notice

The following notice appears on every page of the built site:

> Based on "Lessons in Electric Circuits" by Tony R. Kuphaldt.
> Converted and restyled by the Hearth project, 2026.
> Published under CC BY 4.0.
