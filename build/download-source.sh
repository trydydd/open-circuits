#!/usr/bin/env bash
# download-source.sh — Fetch Kuphaldt's pre-built HTML bundle from ibiblio
#
# Usage:
#   bash build/download-source.sh [--force]
#
# Options:
#   --force   Re-download even if upstream/html/ already exists
#
# On success:
#   - upstream/html/ contains the extracted volume directories
#   - upstream/UPSTREAM-VERSION.txt is updated with snapshot date and URL
#
# Exits non-zero on any download or extraction failure.

set -euo pipefail

SOURCE_URL="https://www.ibiblio.org/kuphaldt/electricCircuits/liechtml.tar.gz"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
UPSTREAM_DIR="${REPO_ROOT}/upstream"
HTML_DIR="${UPSTREAM_DIR}/html"
VERSION_FILE="${UPSTREAM_DIR}/UPSTREAM-VERSION.txt"
TARBALL="${UPSTREAM_DIR}/liechtml.tar.gz"

# Expected volume directories after extraction
EXPECTED_VOLUMES=(DC AC Semi Digital Ref Exper)

FORCE=0
for arg in "$@"; do
    case "$arg" in
        --force) FORCE=1 ;;
        *) echo "Unknown argument: $arg" >&2; exit 1 ;;
    esac
done

# ---- Idempotency check ------------------------------------------------

if [[ -d "${HTML_DIR}" && "${FORCE}" -eq 0 ]]; then
    # Check if at least one expected volume directory is present
    populated=0
    for vol in "${EXPECTED_VOLUMES[@]}"; do
        if [[ -d "${HTML_DIR}/${vol}" ]]; then
            populated=1
            break
        fi
    done

    if [[ "${populated}" -eq 1 ]]; then
        echo "upstream/html/ already populated. Skipping download."
        echo "Use --force to re-download."
        exit 0
    fi
fi

# ---- Dependency check -------------------------------------------------

if command -v curl &>/dev/null; then
    DOWNLOADER="curl"
elif command -v wget &>/dev/null; then
    DOWNLOADER="wget"
else
    echo "Error: neither curl nor wget found. Install one and retry." >&2
    exit 1
fi

# ---- Download ---------------------------------------------------------

echo "Downloading ${SOURCE_URL} ..."

if [[ "${DOWNLOADER}" == "curl" ]]; then
    curl --fail --location --progress-bar \
         --output "${TARBALL}" \
         "${SOURCE_URL}"
else
    wget --show-progress \
         --output-document="${TARBALL}" \
         "${SOURCE_URL}"
fi

if [[ ! -f "${TARBALL}" ]]; then
    echo "Error: download completed but tarball not found at ${TARBALL}" >&2
    exit 1
fi

echo "Download complete: ${TARBALL}"

# ---- Extract ----------------------------------------------------------

echo "Extracting to ${HTML_DIR} ..."

rm -rf "${HTML_DIR}"
mkdir -p "${HTML_DIR}"

tar --extract \
    --file="${TARBALL}" \
    --directory="${HTML_DIR}" \
    --strip-components=0 \
    2>/dev/null || \
tar --extract \
    --file="${TARBALL}" \
    --directory="${HTML_DIR}"

# ---- Validate ---------------------------------------------------------

echo "Validating extracted content ..."

missing=()
for vol in "${EXPECTED_VOLUMES[@]}"; do
    if [[ ! -d "${HTML_DIR}/${vol}" ]]; then
        missing+=("${vol}")
    fi
done

if [[ ${#missing[@]} -gt 0 ]]; then
    echo "Warning: expected volume directories not found: ${missing[*]}" >&2
    echo "Contents of ${HTML_DIR}:" >&2
    ls "${HTML_DIR}" >&2
    echo "The tarball structure may have changed. Proceeding anyway." >&2
fi

# ---- Update version file ----------------------------------------------

SNAPSHOT_DATE="$(date -u +%Y-%m-%d)"

cat > "${VERSION_FILE}" <<EOF
# Upstream Source Version
# Written by build/download-source.sh — do not edit manually.

SOURCE_URL=${SOURCE_URL}
SNAPSHOT_DATE=${SNAPSHOT_DATE}
TARBALL=liechtml.tar.gz
EOF

echo "Updated ${VERSION_FILE} (snapshot date: ${SNAPSHOT_DATE})"

# ---- Clean up tarball -------------------------------------------------

rm -f "${TARBALL}"
echo "Removed tarball."

# ---- Summary ----------------------------------------------------------

echo ""
echo "Done. upstream/html/ contents:"
ls "${HTML_DIR}"
