#!/usr/bin/env bash
# inject-overlay.sh — Inject CSS link, header, and footer into upstream HTML pages.
#
# Usage:
#   bash overlay/inject-overlay.sh <input-dir> <output-dir>
#
# Arguments:
#   input-dir   Directory containing the upstream HTML tree
#               (e.g. upstream/html/ with DC/, AC/, Semi/, ... subdirs)
#   output-dir  Directory to write the modified HTML tree into
#               (e.g. output/html/)
#
# What it does:
#   - Copies every .html file from input-dir into output-dir, preserving
#     subdirectory structure
#   - Inserts <link rel="stylesheet"> into <head>
#   - Injects header.html content after <body>
#   - Injects footer.html content before </body>
#   - Resolves {{PLACEHOLDER}} tokens in the header/footer templates so that
#     paths are correct whether the file is at the root level or one level deep
#   - Copies overlay/css/ and overlay/js/ into output-dir alongside the HTML
#   - After processing, validates that no http:// or https:// URLs appear in the
#     output except inside .oc-footer attribution links; exits non-zero if found.
#
# Exits non-zero on any error.

set -euo pipefail

# ---- Argument validation --------------------------------------------------

if [[ $# -ne 2 ]]; then
    echo "Usage: $0 <input-dir> <output-dir>" >&2
    exit 1
fi

INPUT_DIR="${1%/}"
OUTPUT_DIR="${2%/}"

if [[ ! -d "${INPUT_DIR}" ]]; then
    echo "Error: input directory '${INPUT_DIR}' does not exist." >&2
    exit 1
fi

# ---- Locate repo root and overlay assets ----------------------------------

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

HEADER_TMPL="${SCRIPT_DIR}/templates/header.html"
FOOTER_TMPL="${SCRIPT_DIR}/templates/footer.html"
CSS_SRC="${SCRIPT_DIR}/css"
JS_SRC="${SCRIPT_DIR}/js"

for f in "${HEADER_TMPL}" "${FOOTER_TMPL}"; do
    if [[ ! -f "${f}" ]]; then
        echo "Error: template not found: ${f}" >&2
        exit 1
    fi
done

# ---- Prepare output directory ---------------------------------------------

mkdir -p "${OUTPUT_DIR}"

# ---- Helper: inject into a single file ------------------------------------
# Arguments:
#   $1  absolute path to source .html file
#   $2  absolute path to destination .html file
#   $3  depth (0 = root, 1 = one subdir deep, etc.)

inject_file() {
    local src="$1"
    local dst="$2"
    local depth="$3"

    # Compute relative path prefix based on depth
    local prefix=""
    local i
    for (( i = 0; i < depth; i++ )); do
        prefix="../${prefix}"
    done

    # Resolve template placeholders
    # Inter-volume nav: link to each volume's first chapter or its subdir index
    local idx_path="${prefix}index.html"
    local dc_path="${prefix}DC/DC_1.html"
    local ac_path="${prefix}AC/AC_1.html"
    local semi_path="${prefix}Semi/SEMI_1.html"
    local dig_path="${prefix}Digital/DIGI_1.html"
    local ref_path="${prefix}Ref/REF_1.html"
    local exp_path="${prefix}Exper/EXPER_1.html"
    local license_path="${prefix}LICENSE-DSL.txt"
    local attr_path="${prefix}ATTRIBUTION.md"
    local css_href="${prefix}css/open-circuits.css"

    # Read and substitute header template
    local header_html
    header_html="$(sed \
        -e "s|{{INDEX_PATH}}|${idx_path}|g" \
        -e "s|{{VOL_DC}}|${dc_path}|g" \
        -e "s|{{VOL_AC}}|${ac_path}|g" \
        -e "s|{{VOL_SEMI}}|${semi_path}|g" \
        -e "s|{{VOL_DIGITAL}}|${dig_path}|g" \
        -e "s|{{VOL_REF}}|${ref_path}|g" \
        -e "s|{{VOL_EXPER}}|${exp_path}|g" \
        "${HEADER_TMPL}")"

    # Read and substitute footer template
    local footer_html
    footer_html="$(sed \
        -e "s|{{LICENSE_PATH}}|${license_path}|g" \
        -e "s|{{ATTRIBUTION_PATH}}|${attr_path}|g" \
        "${FOOTER_TMPL}")"

    # Build CSS link tag
    local css_link="<link rel=\"stylesheet\" href=\"${css_href}\">"

    # Process the file with awk:
    #   - Insert CSS link just before </head>
    #   - Insert header just after <body ...>
    #   - Insert footer just before </body>
    awk -v css_link="${css_link}" \
        -v header_html="${header_html}" \
        -v footer_html="${footer_html}" '
    {
        # Insert CSS before </head>
        if (tolower($0) ~ /<\/head>/) {
            print css_link
        }
        # Print the current line
        print
        # Insert header after opening <body> tag
        if (tolower($0) ~ /<body[^>]*>/) {
            print header_html
        }
    }
    # Insert footer before </body> — we buffer and emit at end
    ' "${src}" | awk -v footer_html="${footer_html}" '
    {
        lines[NR] = $0
    }
    END {
        for (i = 1; i <= NR; i++) {
            if (tolower(lines[i]) ~ /<\/body>/) {
                print footer_html
            }
            print lines[i]
        }
    }
    ' > "${dst}"
}

# ---- Walk input dir and process .html files -------------------------------

PAGE_COUNT=0

while IFS= read -r -d '' src_file; do
    # Path of this file relative to INPUT_DIR
    rel_path="${src_file#${INPUT_DIR}/}"

    dst_file="${OUTPUT_DIR}/${rel_path}"
    dst_dir="$(dirname "${dst_file}")"

    # Count directory depth (number of path separators)
    depth=$(echo "${rel_path}" | tr -cd '/' | wc -c)

    mkdir -p "${dst_dir}"
    inject_file "${src_file}" "${dst_file}" "${depth}"
    (( PAGE_COUNT++ )) || true
done < <(find "${INPUT_DIR}" -name "*.html" -print0 | sort -z)

echo "Processed ${PAGE_COUNT} HTML page(s) → ${OUTPUT_DIR}"

# ---- Copy static assets ---------------------------------------------------

if [[ -d "${CSS_SRC}" ]]; then
    mkdir -p "${OUTPUT_DIR}/css"
    cp -r "${CSS_SRC}/." "${OUTPUT_DIR}/css/"
    echo "Copied CSS → ${OUTPUT_DIR}/css/"
fi

if [[ -d "${JS_SRC}" ]] && [[ -n "$(find "${JS_SRC}" -mindepth 1 -maxdepth 1 -not -name '.gitkeep' -print -quit 2>/dev/null)" ]]; then
    mkdir -p "${OUTPUT_DIR}/js"
    cp -r "${JS_SRC}/." "${OUTPUT_DIR}/js/"
    echo "Copied JS → ${OUTPUT_DIR}/js/"
fi

# Copy LICENSE and ATTRIBUTION to output root so relative links work
for f in LICENSE-DSL.txt ATTRIBUTION.md; do
    src="${REPO_ROOT}/${f}"
    if [[ -f "${src}" ]]; then
        cp "${src}" "${OUTPUT_DIR}/${f}"
    fi
done

# ---- Validate: no external URLs outside attribution footer ----------------

echo "Validating output for external URLs..."

# Collect any http:// or https:// occurrences that are NOT inside .oc-footer
EXTERNAL_VIOLATIONS=()

while IFS= read -r -d '' html_file; do
    # Extract lines outside .oc-footer that contain http(s)://
    # Strategy: use awk to skip content between <footer class="oc-footer"> and </footer>
    violations="$(awk '
        /<footer[^>]*oc-footer/ { in_footer=1 }
        !in_footer && /https?:\/\// { print FILENAME ":" NR ": " $0 }
        /<\/footer>/ { in_footer=0 }
    ' "${html_file}")"

    if [[ -n "${violations}" ]]; then
        EXTERNAL_VIOLATIONS+=("${violations}")
    fi
done < <(find "${OUTPUT_DIR}" -name "*.html" -print0 | sort -z)

if [[ ${#EXTERNAL_VIOLATIONS[@]} -gt 0 ]]; then
    echo "WARNING: External URLs found outside .oc-footer in output HTML:" >&2
    printf '%s\n' "${EXTERNAL_VIOLATIONS[@]}" >&2
    echo "Review the above — upstream content may contain external links." >&2
    # Exit non-zero per spec
    exit 1
fi

echo "Validation passed: no external URLs outside attribution footer."
echo "Done."
