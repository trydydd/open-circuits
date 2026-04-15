# Building Open Circuits

## Prerequisites

| Tool | Purpose | Install |
|------|---------|---------|
| `python3` (3.10+) | All build scripts | `sudo apt install python3` / standard on macOS |
| `make` | Makefile shortcuts | `sudo apt install make` / standard on macOS |
| `beautifulsoup4` | HTML injection (`inject_overlay.py`) | installed via `make install` |
| `zimwriterfs` | ZIM packaging (optional) | see below |

The Python dependencies are pinned in `requirements.txt` and installed into a local virtualenv by `make install`. No system-level Python packages are needed.

### Installing zimwriterfs (optional)

`zimwriterfs` is only required to produce `.zim` output. The HTML build works without it.

```sh
# Ubuntu / Debian
sudo apt install zimwriterfs

# macOS
brew install kiwix-tools

# Manual (from source)
# https://github.com/openzim/zim-tools
```

If `zimwriterfs` is not installed, `build/build_zim.py` prints an install hint and exits 0 — the rest of the pipeline continues unaffected.

---

## Local Build

### Option 1 — Makefile (recommended)

```sh
# 1. Create virtualenv and install Python dependencies
make install

# 2. Download upstream HTML from ibiblio (~36 MB, cached after first run)
make download

# 3. Inject overlay (CSS, header, footer) → output/html/
make inject

# 4. Verify content integrity (output text matches upstream)
make verify

# Or run all three in sequence:
make build
```

Run `make help` to see all available targets.

### Option 2 — Python scripts directly

```sh
# Create and activate venv
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt

# Download upstream source
python build/download_source.py

# Inject overlay
python overlay/inject_overlay.py upstream/html output/html

# (Optional) Build ZIM
python build/build_zim.py

# Full pipeline with post-build checks
python build/build_html.py
```

### Flags

| Script | Flag | Effect |
|--------|------|--------|
| `download_source.py` | `--force` | Re-download even if `upstream/html/` is populated |
| `build_html.py` | `--clean` | Delete `output/html/` before building |
| `build_html.py` | `--skip-integrity` | Skip text-content integrity check (faster iteration) |
| `build_zim.py` | `--output PATH` | Write ZIM to a custom path |

---

## Testing the Output

### In a browser

```sh
# Python's built-in server works fine for local testing
cd output/html
python3 -m http.server 8080
# then open http://localhost:8080
```

Check that:
- The root `index.html` loads and the header navigation links work.
- Clicking into a volume (e.g. `DC/DC_1.html`) shows the chapter content with header and footer injected.
- The footer contains links to `LICENSE.txt` and `ATTRIBUTION.md`.
- No pages request external URLs (CSS, fonts, scripts).

### With kiwix-serve (ZIM mode)

```sh
python build/build_zim.py
kiwix-serve output/open-circuits.zim
# then open http://localhost:8080
```

### Automated checks

```sh
# Run the integration test suite
make test

# Content integrity check only (fast)
python build/verify_content_integrity.py upstream/html output/html

# Confirm attribution notice is present on root page
grep -l 'LICENSE.txt\|ATTRIBUTION.md' output/html/index.html
```

---

## Adding or Updating the Overlay CSS

The stylesheet lives at `overlay/css/open-circuits.css`. It is copied into `output/html/css/` during every build — no separate step needed.

**To iterate on styles:**

1. Edit `overlay/css/open-circuits.css`.
2. Run `make inject` (skips the download, fast).
3. Reload `http://localhost:8080` in your browser.

**Constraints to respect:**

- No external URLs. All fonts, icons, and images must be inlined or included as local files. The build validates this and will exit non-zero if an external `<link>` or `<script>` URL is found outside the footer.
- The CSS is injected into every page at every depth (`DC/DC_1.html`, `index.html`, etc.). The path to `css/open-circuits.css` is resolved relative to each file's depth automatically by `inject_overlay.py` — you do not need to manage path prefixes in the stylesheet itself.
- Avoid `@import` rules pointing to external URLs for the same reason.

**To add a new static asset** (e.g. a custom font file or icon):

1. Place the file under `overlay/css/` (for CSS assets) or `overlay/js/` (for scripts).
2. Reference it with a relative path in the CSS or template.
3. `inject_overlay.py` copies the entire `overlay/css/` and `overlay/js/` trees into `output/html/css/` and `output/html/js/` on each build.

---

## Clean Up

```sh
# Remove built output (keeps upstream cache and venv)
make clean

# Remove everything including venv and caches
make clean-all
```

The `upstream/html/` download cache is preserved by `make clean` intentionally — re-downloading 36 MB on every clean would be slow. Use `python build/download_source.py --force` to refresh it.
