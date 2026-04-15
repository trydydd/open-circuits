# Hearth Integration

How the Hearth offline community hub consumes Open Circuits release artifacts.

> This document describes the integration contract. Implementation lives in the `hearth` repo, not here.

---

## Release Artifacts

Each tagged release of this repo produces two artifacts, attached to the GitHub release:

| Artifact | Description |
|----------|-------------|
| `open-circuits-vX.Y.Z.tar.gz` | Self-contained HTML site — served by nginx in static mode |
| `open-circuits.zim` | Kiwix ZIM file — served by kiwix-serve in ZIM mode |

Both are built by `build/build_all.py` and attached by `.github/workflows/release.yml`.

---

## Static Mode (nginx)

### How the Hearth Ansible Role Consumes the Tarball

The `hearth` repo contains an ansible role that:

1. Downloads the pinned release tarball from GitHub releases.
2. Extracts it to a directory on the server (e.g. `/srv/hearth/open-circuits/`).
3. Configures nginx to serve the directory at `/circuits/`.

The `hearth.yaml` configuration (in the `hearth` repo) identifies which release to pin:

```yaml
services:
  open_circuits:
    enabled: true
    version: "v1.0.0"
    mode: static
```

### nginx Path Convention

Content is served at `/circuits/`, following the same path pattern as other Hearth services. The volume chapter paths mirror Kuphaldt's original naming exactly:

```
/circuits/index.html            # Root index — list of all volumes
/circuits/DC/DC_1.html          # Volume I, Chapter 1 — Basic Concepts of Electricity
/circuits/DC/DC_2.html          # Volume I, Chapter 2 — Ohm's Law
/circuits/AC/AC_1.html          # Volume II, Chapter 1 — Basic AC Theory
/circuits/Semi/SEMI_1.html      # Volume III, Chapter 1 — Amplifiers and Active Devices
/circuits/Digital/DIGI_1.html   # Volume IV, Chapter 1 — Numeration Systems
/circuits/Ref/REF_1.html        # Volume V, Chapter 1 — Reference tables
/circuits/Exper/EXPER_1.html    # Volume VI, Chapter 1 — Experiments
```

A minimal nginx location block:

```nginx
location /circuits/ {
    alias /srv/hearth/open-circuits/;
    index index.html;
    try_files $uri $uri/ =404;
}
```

---

## ZIM Mode (Kiwix)

### Where to Place the ZIM File

Place `open-circuits.zim` in the Hearth kiwix library directory alongside other ZIM content:

```
/srv/hearth/kiwix/
├── open-circuits.zim
├── wikipedia_en_all_mini.zim
└── ...
```

The existing Hearth kiwix-serve instance picks it up automatically on restart (or hot-reload, depending on kiwix-serve version).

The `hearth.yaml` configuration for ZIM mode:

```yaml
services:
  open_circuits:
    enabled: true
    version: "v1.0.0"
    mode: kiwix
```

### Kiwix Metadata

The ZIM file is built with metadata from `zim-metadata/metadata.yaml`. It will appear in the Kiwix library as:

- **Title:** Open Circuits — A Portable Electronics Reference
- **Creator:** Tony R. Kuphaldt
- **Publisher:** Hearth Project
- **Language:** English
- **Tags:** electronics; reference; education

---

## URL Stability Contract

**Paths must not change across versions.**

The `salvage-electronics` pathway links into Open Circuits for deep theory references. Any change to the URL structure would break those links. The following paths are stable by contract:

| Volume | Stable URL pattern |
|--------|--------------------|
| DC | `/circuits/DC/DC_{N}.html` |
| AC | `/circuits/AC/AC_{N}.html` |
| Semiconductors | `/circuits/Semi/SEMI_{N}.html` |
| Digital | `/circuits/Digital/DIGI_{N}.html` |
| Reference | `/circuits/Ref/REF_{N}.html` |
| Experiments | `/circuits/Exper/EXPER_{N}.html` |

These paths are preserved by using Kuphaldt's original directory and file naming verbatim. `inject_overlay.py` does not rename or restructure any files — it only adds assets and modifies content in-place.

**Do not:**
- Rename volume directories (e.g. `Semi` → `Semiconductors`).
- Flatten the directory structure.
- Add version prefixes to paths.

If a structural change ever becomes necessary, it must be coordinated with the `salvage-electronics` repo and communicated well in advance of the release.

---

## How salvage-electronics Links In

The `salvage-electronics` pathway uses absolute links of the form:

```
/circuits/DC/DC_5.html          # Series and Parallel Circuits
/circuits/AC/AC_7.html          # Filters
/circuits/Semi/SEMI_3.html      # Diodes and Rectifiers
/circuits/Exper/EXPER_1.html    # Lab experiments
```

Volume VI (Experiments) is the primary crossover point — its lab exercises overlap directly with salvage-electronics hands-on content. When writing pathway content that references theory, prefer linking to specific chapter files rather than to the root index.

---

## Upgrading to a New Release

To update the pinned version on a Hearth deployment:

1. Tag a new release in this repo (e.g. `v1.1.0`).
2. Confirm the release workflow attached the expected artifacts.
3. Update `version:` in `hearth.yaml` in the `hearth` repo.
4. Run the Hearth ansible playbook — it downloads the new tarball and restarts nginx (or replaces the ZIM and restarts kiwix-serve).

No path changes occur between minor versions. Chapter files that existed in the previous version continue to exist at the same paths.
