# Open Circuits — Claude Context

## Project

A portable web edition of Tony R. Kuphaldt's *Lessons in Electric Circuits* (6 volumes: DC, AC, Semiconductors, Digital, Reference, Experiments). Packages as static HTML site and ZIM file for offline/Kiwix use. Part of the Hearth offline community hub project.

**Key constraint**: All output is fully self-contained — no CDN dependencies, no external URLs.

## Stack

- **Python 3.9+** build pipeline
- **BeautifulSoup** for HTML injection
- **GitHub Actions** for CI, Pages, and release
- No JS framework — vanilla JS only

## Build Commands

```bash
make install    # create venv + install deps
make build      # download + inject + verify
make test       # run pytest
```

## Key Files

- `overlay/css/open-circuits.css` — main stylesheet (injected into every page)
- `overlay/js/navigation.js` — sidebar TOC + chapter navigation (vanilla JS)
- `overlay/templates/header.html` — injected at top of `<body>`
- `overlay/templates/footer.html` — injected before `</body>`
- `overlay/fonts/` — bundled WOFF2 fonts (Vollkorn + Chivo)
- `overlay/inject_overlay.py` — injection script (CSS, JS, fonts, templates)
- `build/build_html.py` — HTML build pipeline
- `open-circuits-spec.md` — full project specification

## Upstream HTML Quirks

Kuphaldt's HTML is HTML4 Transitional with these patterns to be aware of:
- Chapter headings: `<h2><u><a name="xtocidXXXXX">Title</a></u></h2>`
- Image navigation: `<a href="..."><img src=previous.jpg alt="Previous"></a>`
- A second `<body bgColor=white>` tag inside the body (browsers handle gracefully)
- Chapter files: `DC/DC_1.html` through `DC/DC_16.html` etc.

## URL Path Convention

```
DC/DC_N.html       — DC volume chapters
AC/AC_N.html       — AC volume chapters
Semi/SEMI_N.html   — Semiconductors
Digital/DIGI_N.html — Digital
Ref/REF_1.html     — Reference
Exper/EXP_1.html — Experiments
```

Paths must remain stable across versions (Hearth integration depends on them).

---

## Design Context

### Users
Everyone — regardless of technical background, device quality, or economic context. Open Circuits is part of a broader effort (the Hearth project) to teach salvage electronics to anyone who wants to learn, in a world where the internet is increasingly hostile and pro-consumerism. Users might be sitting at a workbench with a cheap Android phone, reading on a secondhand laptop in low light, or studying on a proper desktop. The interface must respect all of them equally.

Primary job to be done: read a chapter, look up a reference value, follow an experiment. Deep focus, sustained reading, technical lookup.

### Brand Personality
**Tactile · generous · honest**

Warm and workshop-y — feels like a well-used repair manual or technical zine. Made by hands, for hands. Inviting and a little rough around the edges. Cares about the reader without performing that care. The content is the point; the interface is in service of it.

Anti-references: corporate developer docs (sterile, performative), AI-generated design (glassmorphism, cyan-on-dark, gradient text), premium magazine layouts (too precious), generic textbook portals (institutional and cold).

### Aesthetic Direction
- **Theme**: Light default with automatic dark mode via `prefers-color-scheme`. No JS toggle needed.
- **Palette**: Warm cream/paper tones (not pure white), deep warm charcoal (not pure black), copper/amber as the single accent — the color of solder, component markings, copper wire. OKLCH throughout.
- **Typography**: Bundled WOFF2 fonts. Vollkorn (old-style serif) for body, Chivo (blunt grotesque) for headings/UI. Both self-hosted in `overlay/fonts/`.
- **Texture**: Subtle — warm neutrals and spacing rhythm create the workshop feel, not literal textures or decorative borders.

### Design Principles
1. **Serve the text, not the brand.** The interface disappears into the reading experience. Kuphaldt's content is what matters.
2. **Dignified utility.** Every element earns its place. Nothing decorative for its own sake. Warmth comes from type, color temperature, and rhythm.
3. **Works everywhere.** Readable on a €30 Android phone. Legible in direct sunlight. Functional with no JavaScript. Print-friendly by default.
4. **Offline-first aesthetics.** No design choices that imply connectivity. Everything ships in the build.
5. **Respect, not condescension.** The reader is smart. The interface doesn't explain itself or add unnecessary friction.
