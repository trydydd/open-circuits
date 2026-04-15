#!/usr/bin/env bash
# verify-content-integrity.sh
#
# Verifies that the text content of every HTML page in the output matches the
# corresponding upstream source page — ensuring the overlay injection process
# has not altered, duplicated, or dropped any of Kuphaldt's original text.
#
# How it works:
#   For each .html file in <upstream-dir>:
#     1. Strip all HTML tags → normalised upstream text
#     2. Load the matching file from <output-dir>, remove the injected
#        .oc-header and .oc-footer blocks, strip remaining tags → normalised
#        output text
#     3. Compare the two; report any difference as a failure
#
# Usage:
#   bash build/verify-content-integrity.sh [options] [upstream-dir [output-dir]]
#
# Options:
#   --diff    Print a short diff for each failing page
#
# Defaults:
#   upstream-dir  upstream/html
#   output-dir    output/html
#
# Exit codes:
#   0  All pages match
#   1  One or more pages have differing text content

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# ---- Argument parsing -------------------------------------------------------

SHOW_DIFF=0
POSITIONAL=()

for arg in "$@"; do
    case "$arg" in
        --diff) SHOW_DIFF=1 ;;
        --help|-h)
            sed -n '2,/^[^#]/{ /^#/{ s/^# \?//; p }; /^[^#]/q }' "$0"
            exit 0
            ;;
        *) POSITIONAL+=("$arg") ;;
    esac
done

UPSTREAM_DIR="${POSITIONAL[0]:-${REPO_ROOT}/upstream/html}"
OUTPUT_DIR="${POSITIONAL[1]:-${REPO_ROOT}/output/html}"

# Resolve relative paths against repo root
[[ "${UPSTREAM_DIR}" != /* ]] && UPSTREAM_DIR="${REPO_ROOT}/${UPSTREAM_DIR}"
[[ "${OUTPUT_DIR}"   != /* ]] && OUTPUT_DIR="${REPO_ROOT}/${OUTPUT_DIR}"

# ---- Pre-flight checks ------------------------------------------------------

if [[ ! -d "${UPSTREAM_DIR}" ]]; then
    echo "Error: upstream directory not found: ${UPSTREAM_DIR}" >&2
    echo "Run build/download-source.sh first." >&2
    exit 1
fi

if [[ ! -d "${OUTPUT_DIR}" ]]; then
    echo "Error: output directory not found: ${OUTPUT_DIR}" >&2
    echo "Run build/build-html.sh first." >&2
    exit 1
fi

# ---- Text extraction --------------------------------------------------------
#
# extract_text <file>
#
# Produces one normalised word/token per line, with blank lines removed.
# Designed to be identical for the upstream file and its injected counterpart —
# the only differences allowed are the oc-header and oc-footer blocks, which
# are removed before comparison.

extract_text() {
    local file="$1"

    # Step 1: remove injected overlay blocks (no-op on upstream files that
    #         don't contain these class names)
    awk '
        /class="oc-header"/ { skip=1; next }
        /class="oc-footer"/ { skip=1; next }
        skip && /<\/header>/  { skip=0; next }
        skip && /<\/footer>/  { skip=0; next }
        !skip { print }
    ' "${file}" \
    | sed 's/<[^>]*>//g' \
    | tr -s '[:space:]' '\n' \
    | sed '/^[[:space:]]*$/d'
}

# ---- Main comparison loop ---------------------------------------------------

PASS=0
FAIL=0
MISSING=0

while IFS= read -r -d '' upstream_file; do
    rel="${upstream_file#${UPSTREAM_DIR}/}"
    output_file="${OUTPUT_DIR}/${rel}"

    if [[ ! -f "${output_file}" ]]; then
        printf 'MISSING  %s\n' "${rel}"
        (( MISSING++ )) || true
        continue
    fi

    upstream_text="$(extract_text "${upstream_file}")"
    output_text="$(extract_text "${output_file}")"

    if [[ "${upstream_text}" == "${output_text}" ]]; then
        (( PASS++ )) || true
    else
        printf 'FAIL     %s\n' "${rel}"
        (( FAIL++ )) || true

        if [[ "${SHOW_DIFF}" -eq 1 ]]; then
            echo "  --- upstream"
            echo "  +++ output"
            diff \
                <(echo "${upstream_text}") \
                <(echo "${output_text}") \
                | grep '^[<>]' \
                | head -20 \
                | sed 's/^/  /'
            echo ""
        fi
    fi
done < <(find "${UPSTREAM_DIR}" -name "*.html" -print0 | sort -z)

# ---- Summary ----------------------------------------------------------------

echo ""
echo "Upstream : ${UPSTREAM_DIR}"
echo "Output   : ${OUTPUT_DIR}"
printf 'Results  : %d passed, %d failed, %d missing\n' \
    "${PASS}" "${FAIL}" "${MISSING}"

if [[ "${FAIL}" -gt 0 || "${MISSING}" -gt 0 ]]; then
    echo ""
    echo "CONTENT INTEGRITY CHECK FAILED" >&2
    [[ "${SHOW_DIFF}" -eq 0 && "${FAIL}" -gt 0 ]] && \
        echo "Re-run with --diff to see what changed." >&2
    exit 1
fi

echo ""
echo "CONTENT INTEGRITY CHECK PASSED"
