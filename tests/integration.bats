#!/usr/bin/env bats
# tests/integration.bats
#
# End-to-end integration tests for Open Circuits, Phases 1–4.
#
# Runs the full pipeline against real upstream data — no mocks, no synthetic
# pages.  Requires internet access to download the Kuphaldt HTML bundle from
# ibiblio.org on first run (~36 MB).  Subsequent runs reuse the cached
# upstream/html/ tree.
#
# Run:
#   bats tests/integration.bats
#
# The injected HTML is written to output/test-html/ and removed on teardown.

# ---------------------------------------------------------------------------
# Suite setup / teardown (runs once for the whole file)
# ---------------------------------------------------------------------------

setup_file() {
    # Compute REPO_ROOT from the test file's own path (BATS_TEST_FILENAME is
    # set by bats to the absolute path of this file).
    export REPO_ROOT
    REPO_ROOT="$(cd "$(dirname "$BATS_TEST_FILENAME")/.." && pwd)"
    export TEST_OUT="${REPO_ROOT}/output/test-html"

    # Phase 2: fetch the real upstream HTML bundle.
    # Idempotent — skips the download if upstream/html/ is already populated.
    bash "${REPO_ROOT}/build/download-source.sh"

    # Phase 4: inject the overlay into the real HTML tree.
    rm -rf "${TEST_OUT}"
    bash "${REPO_ROOT}/overlay/inject-overlay.sh" \
        "${REPO_ROOT}/upstream/html" "${TEST_OUT}"
}

teardown_file() {
    rm -rf "${TEST_OUT}"
}

# ---------------------------------------------------------------------------
# Phase 1: Foundation — repo scaffolding and legal files
# ---------------------------------------------------------------------------

@test "phase1: upstream/ directory exists" {
    [ -d "${REPO_ROOT}/upstream" ]
}

@test "phase1: build/ directory exists" {
    [ -d "${REPO_ROOT}/build" ]
}

@test "phase1: overlay/css/ directory exists" {
    [ -d "${REPO_ROOT}/overlay/css" ]
}

@test "phase1: overlay/js/ directory exists" {
    [ -d "${REPO_ROOT}/overlay/js" ]
}

@test "phase1: overlay/templates/ directory exists" {
    [ -d "${REPO_ROOT}/overlay/templates" ]
}

@test "phase1: output/ directory exists" {
    [ -d "${REPO_ROOT}/output" ]
}

@test "phase1: zim-metadata/ directory exists" {
    [ -d "${REPO_ROOT}/zim-metadata" ]
}

@test "phase1: .github/workflows/ directory exists" {
    [ -d "${REPO_ROOT}/.github/workflows" ]
}

@test "phase1: docs/ directory exists" {
    [ -d "${REPO_ROOT}/docs" ]
}

@test "phase1: LICENSE.txt is non-empty" {
    [ -s "${REPO_ROOT}/LICENSE.txt" ]
}

@test "phase1: LICENSE.txt identifies CC BY 4.0" {
    grep -qi "creative commons" "${REPO_ROOT}/LICENSE.txt"
    grep -qi "4\.0" "${REPO_ROOT}/LICENSE.txt"
}

@test "phase1: ATTRIBUTION.md is non-empty" {
    [ -s "${REPO_ROOT}/ATTRIBUTION.md" ]
}

@test "phase1: ATTRIBUTION.md credits Kuphaldt" {
    grep -qi "kuphaldt" "${REPO_ROOT}/ATTRIBUTION.md"
}

@test "phase1: ATTRIBUTION.md references CC BY 4.0" {
    grep -qi "creative commons\|CC BY" "${REPO_ROOT}/ATTRIBUTION.md"
}

@test "phase1: README.md is non-empty" {
    [ -s "${REPO_ROOT}/README.md" ]
}

@test "phase1: output/.gitignore exists" {
    [ -f "${REPO_ROOT}/output/.gitignore" ]
}

# ---------------------------------------------------------------------------
# Phase 2: Download pipeline
# ---------------------------------------------------------------------------

@test "phase2: upstream/html/ was created by download-source.sh" {
    [ -d "${REPO_ROOT}/upstream/html" ]
}

@test "phase2: DC volume directory exists in upstream/html/" {
    [ -d "${REPO_ROOT}/upstream/html/DC" ]
}

@test "phase2: AC volume directory exists in upstream/html/" {
    [ -d "${REPO_ROOT}/upstream/html/AC" ]
}

@test "phase2: Semi volume directory exists in upstream/html/" {
    [ -d "${REPO_ROOT}/upstream/html/Semi" ]
}

@test "phase2: Digital volume directory exists in upstream/html/" {
    [ -d "${REPO_ROOT}/upstream/html/Digital" ]
}

@test "phase2: Ref volume directory exists in upstream/html/" {
    [ -d "${REPO_ROOT}/upstream/html/Ref" ]
}

@test "phase2: Exper volume directory exists in upstream/html/" {
    [ -d "${REPO_ROOT}/upstream/html/Exper" ]
}

@test "phase2: upstream/html/ contains HTML files" {
    local count
    count=$(find "${REPO_ROOT}/upstream/html" -name "*.html" | wc -l)
    [ "$count" -gt 0 ]
}

@test "phase2: UPSTREAM-VERSION.txt records SOURCE_URL" {
    grep -q "^SOURCE_URL=" "${REPO_ROOT}/upstream/UPSTREAM-VERSION.txt"
}

@test "phase2: UPSTREAM-VERSION.txt records SNAPSHOT_DATE" {
    grep -qE "^SNAPSHOT_DATE=[0-9]{4}-[0-9]{2}-[0-9]{2}" \
        "${REPO_ROOT}/upstream/UPSTREAM-VERSION.txt"
}

@test "phase2: download-source.sh is idempotent — skips when already populated" {
    run bash "${REPO_ROOT}/build/download-source.sh"
    [ "$status" -eq 0 ]
    [[ "$output" == *"already populated"* ]]
}

@test "phase2: DC/DC_1.html exists (first chapter of first volume)" {
    [ -f "${REPO_ROOT}/upstream/html/DC/DC_1.html" ]
}

# ---------------------------------------------------------------------------
# Phase 3: Overlay assets
# ---------------------------------------------------------------------------

@test "phase3: overlay/css/open-circuits.css exists" {
    [ -f "${REPO_ROOT}/overlay/css/open-circuits.css" ]
}

@test "phase3: CSS file contains no external http(s) URLs" {
    ! grep -qiE 'https?://' "${REPO_ROOT}/overlay/css/open-circuits.css"
}

@test "phase3: CSS defines max-width body constraint" {
    grep -q "max-width" "${REPO_ROOT}/overlay/css/open-circuits.css"
}

@test "phase3: CSS defines .oc-header styles" {
    grep -q "oc-header" "${REPO_ROOT}/overlay/css/open-circuits.css"
}

@test "phase3: CSS defines .oc-footer styles" {
    grep -q "oc-footer" "${REPO_ROOT}/overlay/css/open-circuits.css"
}

@test "phase3: CSS includes a responsive @media query" {
    grep -q "@media" "${REPO_ROOT}/overlay/css/open-circuits.css"
}

@test "phase3: overlay/templates/header.html exists" {
    [ -f "${REPO_ROOT}/overlay/templates/header.html" ]
}

@test "phase3: header template carries {{INDEX_PATH}} placeholder" {
    grep -q "{{INDEX_PATH}}" "${REPO_ROOT}/overlay/templates/header.html"
}

@test "phase3: header template carries all six volume placeholders" {
    for ph in VOL_DC VOL_AC VOL_SEMI VOL_DIGITAL VOL_REF VOL_EXPER; do
        grep -q "{{${ph}}}" "${REPO_ROOT}/overlay/templates/header.html"
    done
}

@test "phase3: overlay/templates/footer.html exists" {
    [ -f "${REPO_ROOT}/overlay/templates/footer.html" ]
}

@test "phase3: footer template carries {{LICENSE_PATH}} placeholder" {
    grep -q "{{LICENSE_PATH}}" "${REPO_ROOT}/overlay/templates/footer.html"
}

@test "phase3: footer template carries {{ATTRIBUTION_PATH}} placeholder" {
    grep -q "{{ATTRIBUTION_PATH}}" "${REPO_ROOT}/overlay/templates/footer.html"
}

@test "phase3: footer template references both license and attribution links" {
    grep -q "LICENSE_PATH" "${REPO_ROOT}/overlay/templates/footer.html"
    grep -q "ATTRIBUTION_PATH" "${REPO_ROOT}/overlay/templates/footer.html"
}

# ---------------------------------------------------------------------------
# Phase 4: Overlay injection
# ---------------------------------------------------------------------------

@test "phase4: inject-overlay.sh is executable" {
    [ -x "${REPO_ROOT}/overlay/inject-overlay.sh" ]
}

@test "phase4: output/test-html/ was produced" {
    [ -d "${TEST_OUT}" ]
}

@test "phase4: DC volume directory exists in output" {
    [ -d "${TEST_OUT}/DC" ]
}

@test "phase4: AC volume directory exists in output" {
    [ -d "${TEST_OUT}/AC" ]
}

@test "phase4: Semi volume directory exists in output" {
    [ -d "${TEST_OUT}/Semi" ]
}

@test "phase4: Digital volume directory exists in output" {
    [ -d "${TEST_OUT}/Digital" ]
}

@test "phase4: Ref volume directory exists in output" {
    [ -d "${TEST_OUT}/Ref" ]
}

@test "phase4: Exper volume directory exists in output" {
    [ -d "${TEST_OUT}/Exper" ]
}

@test "phase4: output contains at least as many HTML files as input" {
    local in_count out_count
    in_count=$(find "${REPO_ROOT}/upstream/html" -name "*.html" | wc -l)
    out_count=$(find "${TEST_OUT}" -name "*.html" | wc -l)
    [ "$out_count" -ge "$in_count" ]
}

@test "phase4: CSS file is copied to output/css/" {
    [ -f "${TEST_OUT}/css/open-circuits.css" ]
}

@test "phase4: LICENSE.txt is copied to output root" {
    [ -f "${TEST_OUT}/LICENSE.txt" ]
}

@test "phase4: ATTRIBUTION.md is copied to output root" {
    [ -f "${TEST_OUT}/ATTRIBUTION.md" ]
}

@test "phase4: DC/DC_1.html exists in output" {
    [ -f "${TEST_OUT}/DC/DC_1.html" ]
}

@test "phase4: CSS link inserted in a root-level page (depth 0)" {
    local page
    page=$(find "${TEST_OUT}" -maxdepth 1 -name "*.html" | sort | head -1)
    [ -n "$page" ]
    grep -q '<link rel="stylesheet" href="css/open-circuits.css">' "$page"
}

@test "phase4: CSS link uses depth-relative path in a volume subdir page (depth 1)" {
    local page
    page=$(find "${TEST_OUT}" -mindepth 2 -maxdepth 2 -name "*.html" | sort | head -1)
    [ -n "$page" ]
    grep -q '<link rel="stylesheet" href="../css/open-circuits.css">' "$page"
}

@test "phase4: .oc-header is injected in output pages" {
    local page
    page=$(find "${TEST_OUT}" -mindepth 2 -maxdepth 2 -name "*.html" | sort | head -1)
    [ -n "$page" ]
    grep -q 'class="oc-header"' "$page"
}

@test "phase4: .oc-footer is injected in output pages" {
    local page
    page=$(find "${TEST_OUT}" -mindepth 2 -maxdepth 2 -name "*.html" | sort | head -1)
    [ -n "$page" ]
    grep -q 'class="oc-footer"' "$page"
}

@test "phase4: root page nav links have no leading ../ prefix" {
    local page
    page=$(find "${TEST_OUT}" -maxdepth 1 -name "*.html" | sort | head -1)
    [ -n "$page" ]
    # CSS path must not start with ../ at root depth
    ! grep -q 'href="../css/' "$page"
}

@test "phase4: subdir page site-title links back up one level (../index.html)" {
    local page
    page=$(find "${TEST_OUT}" -mindepth 2 -maxdepth 2 -name "*.html" | sort | head -1)
    [ -n "$page" ]
    grep -q 'href="../index.html"' "$page"
}

@test "phase4: subdir page volume nav links include ../ prefix" {
    local page
    page=$(find "${TEST_OUT}" -mindepth 2 -maxdepth 2 -name "*.html" | sort | head -1)
    [ -n "$page" ]
    grep -q 'href="../DC/DC_1.html"' "$page"
}

@test "phase4: footer links in subdir page use ../ relative paths" {
    local page
    page=$(find "${TEST_OUT}" -mindepth 2 -maxdepth 2 -name "*.html" | sort | head -1)
    [ -n "$page" ]
    grep -q 'href="../LICENSE.txt"' "$page"
    grep -q 'href="../ATTRIBUTION.md"' "$page"
}

@test "phase4: footer links in root page use bare relative paths" {
    local page
    page=$(find "${TEST_OUT}" -maxdepth 1 -name "*.html" | sort | head -1)
    [ -n "$page" ]
    grep -q 'href="LICENSE.txt"' "$page"
    grep -q 'href="ATTRIBUTION.md"' "$page"
}

@test "phase4: header appears before footer in every output page" {
    local page fail=0
    while IFS= read -r page; do
        local hline fline
        hline=$(grep -n 'class="oc-header"' "$page" | head -1 | cut -d: -f1)
        fline=$(grep -n 'class="oc-footer"' "$page" | head -1 | cut -d: -f1)
        if [[ -z "$hline" || -z "$fline" || "$hline" -ge "$fline" ]]; then
            echo "ordering problem: $page (header line $hline, footer line $fline)" >&2
            fail=1
        fi
    done < <(find "${TEST_OUT}" -name "*.html" | sort)
    [ "$fail" -eq 0 ]
}

@test "phase4: validator rejects a page with an external <link> resource" {
    local tmpdir outdir
    tmpdir=$(mktemp -d)
    outdir=$(mktemp -d)
    cat > "${tmpdir}/bad.html" <<'HTML'
<html>
<head><link rel="stylesheet" href="https://cdn.example.com/bad.css"></head>
<body><p>Content</p></body>
</html>
HTML
    run bash "${REPO_ROOT}/overlay/inject-overlay.sh" "${tmpdir}" "${outdir}"
    rm -rf "${tmpdir}" "${outdir}"
    [ "$status" -ne 0 ]
    [[ "$output" == *"External resource URLs"* ]]
}

@test "phase4: validator rejects a page with an external <script> resource" {
    local tmpdir outdir
    tmpdir=$(mktemp -d)
    outdir=$(mktemp -d)
    cat > "${tmpdir}/bad.html" <<'HTML'
<html>
<head></head>
<body><script src="https://cdn.example.com/tracker.js"></script><p>Hi</p></body>
</html>
HTML
    run bash "${REPO_ROOT}/overlay/inject-overlay.sh" "${tmpdir}" "${outdir}"
    rm -rf "${tmpdir}" "${outdir}"
    [ "$status" -ne 0 ]
}

@test "phase4: validator passes a page that only has external <a href> hyperlinks" {
    local tmpdir outdir
    tmpdir=$(mktemp -d)
    outdir=$(mktemp -d)
    cat > "${tmpdir}/ok.html" <<'HTML'
<html>
<head><title>Test</title></head>
<body><p>See <a href="https://www.ibiblio.org/">ibiblio</a> for source.</p></body>
</html>
HTML
    run bash "${REPO_ROOT}/overlay/inject-overlay.sh" "${tmpdir}" "${outdir}"
    rm -rf "${tmpdir}" "${outdir}"
    [ "$status" -eq 0 ]
}

@test "phase4: inject-overlay.sh exits non-zero with no arguments" {
    run bash "${REPO_ROOT}/overlay/inject-overlay.sh"
    [ "$status" -ne 0 ]
}

@test "phase4: inject-overlay.sh exits non-zero with a nonexistent input dir" {
    run bash "${REPO_ROOT}/overlay/inject-overlay.sh" /no/such/dir /tmp/out
    [ "$status" -ne 0 ]
}

# ---------------------------------------------------------------------------
# Content integrity verification
# ---------------------------------------------------------------------------

@test "integrity: verify-content-integrity.sh is executable" {
    [ -x "${REPO_ROOT}/build/verify-content-integrity.sh" ]
}

@test "integrity: passes when output matches upstream text" {
    run bash "${REPO_ROOT}/build/verify-content-integrity.sh" \
        "${REPO_ROOT}/upstream/html" "${TEST_OUT}"
    [ "$status" -eq 0 ]
    [[ "$output" == *"INTEGRITY CHECK PASSED"* ]]
}

@test "integrity: reports correct page count" {
    local page_count
    page_count=$(find "${REPO_ROOT}/upstream/html" -name "*.html" | wc -l)
    run bash "${REPO_ROOT}/build/verify-content-integrity.sh" \
        "${REPO_ROOT}/upstream/html" "${TEST_OUT}"
    [ "$status" -eq 0 ]
    [[ "$output" == *"${page_count} passed"* ]]
}

@test "integrity: detects tampered text in output page" {
    local tmpinput tmpoutput
    tmpinput=$(mktemp -d)
    tmpoutput=$(mktemp -d)

    cat > "${tmpinput}/index.html" <<'HTML'
<html><head><title>T</title></head><body><p>Original text here.</p></body></html>
HTML
    bash "${REPO_ROOT}/overlay/inject-overlay.sh" "${tmpinput}" "${tmpoutput}" \
        > /dev/null 2>&1

    # Tamper with output
    sed -i 's/Original/TAMPERED/' "${tmpoutput}/index.html"

    run bash "${REPO_ROOT}/build/verify-content-integrity.sh" "${tmpinput}" "${tmpoutput}"
    rm -rf "${tmpinput}" "${tmpoutput}"
    [ "$status" -ne 0 ]
    [[ "$output" == *"FAIL"* ]]
}

@test "integrity: --diff flag shows what changed" {
    local tmpinput tmpoutput
    tmpinput=$(mktemp -d)
    tmpoutput=$(mktemp -d)

    cat > "${tmpinput}/index.html" <<'HTML'
<html><head><title>T</title></head><body><p>Hello world.</p></body></html>
HTML
    bash "${REPO_ROOT}/overlay/inject-overlay.sh" "${tmpinput}" "${tmpoutput}" \
        > /dev/null 2>&1
    sed -i 's/Hello/Goodbye/' "${tmpoutput}/index.html"

    run bash "${REPO_ROOT}/build/verify-content-integrity.sh" \
        --diff "${tmpinput}" "${tmpoutput}"
    rm -rf "${tmpinput}" "${tmpoutput}"
    [ "$status" -ne 0 ]
    [[ "$output" == *"Hello"* ]] || [[ "$output" == *"Goodbye"* ]]
}

@test "integrity: detects missing output page" {
    local tmpinput tmpoutput
    tmpinput=$(mktemp -d)
    tmpoutput=$(mktemp -d)
    mkdir -p "${tmpinput}/sub"

    cat > "${tmpinput}/index.html" <<'HTML'
<html><head></head><body><p>Root.</p></body></html>
HTML
    cat > "${tmpinput}/sub/page.html" <<'HTML'
<html><head></head><body><p>Sub page.</p></body></html>
HTML
    bash "${REPO_ROOT}/overlay/inject-overlay.sh" "${tmpinput}" "${tmpoutput}" \
        > /dev/null 2>&1
    rm "${tmpoutput}/sub/page.html"

    run bash "${REPO_ROOT}/build/verify-content-integrity.sh" "${tmpinput}" "${tmpoutput}"
    rm -rf "${tmpinput}" "${tmpoutput}"
    [ "$status" -ne 0 ]
    [[ "$output" == *"MISSING"* ]]
}

@test "integrity: exits non-zero for missing upstream dir" {
    run bash "${REPO_ROOT}/build/verify-content-integrity.sh" /no/such/dir /tmp/out
    [ "$status" -ne 0 ]
}

@test "integrity: exits non-zero for missing output dir" {
    run bash "${REPO_ROOT}/build/verify-content-integrity.sh" \
        "${REPO_ROOT}/upstream/html" /no/such/dir
    [ "$status" -ne 0 ]
}
