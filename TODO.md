# Open Circuits — Rebranding Tasks

Tasks to complete the rebrand from Kuphaldt's upstream HTML to the Open Circuits identity.
Ordered by dependency. Parallel-safe tasks are marked.

---

## Task 1: Logo and brand style guide ✓ done

Create the Open Circuits visual identity.

**Deliverables:**
- `overlay/logo.svg` — primary mark. Circuit node / open loop motif. Copper/amber
  fill (`oklch(55% 0.13 65)` approx.), warm charcoal background. Feels hand-drawn,
  workshop-y. No glassmorphism. No gradients. Honest geometry.
- `overlay/brand-guide.md` — one-page style reference:
  - Logo usage (minimum size, clear space, placement)
  - Palette: cream bg, charcoal text, copper accent (hex + OKLCH values from CSS)
  - Typography: Vollkorn (body), Chivo (UI/headings) — sizes, weights, rhythm
  - Tone: tactile, generous, honest. Anti-patterns listed in `.impeccable.md`
- `zim-metadata/favicon.png` — 48×48 px derived from logo (replace 123-byte placeholder)
- `zim-metadata/illustration.png` — 315×250 px branded splash for Kiwix catalog

**Reference files:**
- `CLAUDE.md` → Design Context section
- `.impeccable.md` → full design document
- `overlay/css/open-circuits.css` → live OKLCH palette values (lines 53–128)

---

## Task 2: Strip ibiblio badges and upstream bottom-of-page banners — parallel-safe

The upstream HTML contains external badge links at the bottom of pages:
- `<a href="http://www.ibiblio.org"><img ...></a>` — ibiblio hosting badge
- W3C HTML validation badges (`validator.w3.org`)
- Other "alliant.png", "gnu.png", "linuxppc.png" style hosted-at images

**Fix:** In `overlay/inject_overlay.py`, add a BeautifulSoup stripping pass inside
`inject_file()` to remove `<a>` tags whose `href` matches `ibiblio.org`,
`validator.w3.org`, or `gnu.org`, plus any lone `<img>` badges in external-link
anchors near the bottom of `<body>`. BeautifulSoup is already available (used in
`validate_no_external_resources`).

**File:** `overlay/inject_overlay.py`

---

## Task 3: Rewrite page `<title>` tags — parallel-safe

Upstream titles read: `"Lessons In Electric Circuits -- Volume I (DC) -- Chapter N: ..."`

Desired: `"Open Circuits — <chapter title>"`

**Fix:** In `inject_file()` in `overlay/inject_overlay.py`, add a regex substitution
after reading content:
```python
content = re.sub(
    r"<title>Lessons In Electric Circuits[^<]*?:\s*([^<]+)</title>",
    r"<title>Open Circuits \u2014 \1</title>",
    content, flags=re.IGNORECASE
)
```
Handle the index page separately if it uses a different title pattern.

**File:** `overlay/inject_overlay.py`

---

## Task 4: Add logo to header — depends on Task 1

Once `overlay/logo.svg` exists:
- Inline or `<img>`-reference the logo in `overlay/templates/header.html` next to
  the `.oc-site-title` text (or replace text with logo + wordmark).
- Copy `overlay/logo.svg` to output in `inject_overlay.py` (alongside CSS/JS/fonts
  copy block).

**Files:** `overlay/templates/header.html`, `overlay/inject_overlay.py`

---

## Task 5: Strip original volume title headers from page body — parallel-safe

Kuphaldt's chapter pages open with a large bold heading reading
"Lessons In Electric Circuits — Volume I" before chapter content begins. This is
redundant with our header bar.

**Fix:** In `inject_file()`, after header injection, use BeautifulSoup to detect
and remove the first `<h1>` (or bold block) containing "Lessons In Electric Circuits"
if it appears within the first ~500 characters of body content.

**File:** `overlay/inject_overlay.py`

---

## Task 6: Update ZIM metadata branding — depends on Task 1

Review `zim-metadata/metadata.yaml`:
- Confirm `Title` is "Open Circuits"
- Confirm `Description` does not mention ibiblio
- Update `Favicon` / `Illustration` paths once Task 1 assets are in place

**File:** `zim-metadata/metadata.yaml`

---

## Verification

After each task:
```bash
make build
grep -i "ibiblio" output/html/DC/DC_1.html   # should return nothing
grep "<title>" output/html/DC/DC_1.html       # should say "Open Circuits —"
```

Full suite:
```bash
make test
```
