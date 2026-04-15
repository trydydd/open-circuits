PYTHON  := $(shell command -v python3 2>/dev/null || command -v python)
VENV    := .venv
VP      := $(VENV)/bin/python
PIP     := $(VENV)/bin/pip
PYTEST  := $(VENV)/bin/pytest

# ── Environment ────────────────────────────────────────────────────────────────

$(VENV): requirements-dev.txt requirements.txt
	$(PYTHON) -m venv $(VENV)
	$(PIP) install --quiet --upgrade pip
	$(PIP) install --quiet -r requirements-dev.txt
	@touch $(VENV)

.PHONY: install
install: $(VENV)  ## Create venv and install all dependencies

# ── Pipeline ───────────────────────────────────────────────────────────────────

.PHONY: download
download: $(VENV)  ## Fetch upstream HTML bundle from ibiblio (idempotent)
	$(VP) build/download_source.py

.PHONY: inject
inject: $(VENV)  ## Inject overlay into upstream HTML → output/html/
	$(VP) overlay/inject_overlay.py upstream/html output/html

.PHONY: verify
verify: $(VENV)  ## Verify output text matches upstream (no content drift)
	$(VP) build/verify_content_integrity.py

.PHONY: build
build: download inject verify  ## Full pipeline: download → inject → verify

# ── Tests ──────────────────────────────────────────────────────────────────────

.PHONY: test
test: $(VENV)  ## Run the integration test suite
	$(PYTEST) tests/ -v

# ── Housekeeping ───────────────────────────────────────────────────────────────

.PHONY: clean
clean:  ## Remove built output (keeps upstream cache and venv)
	rm -rf output/html output/test-html

.PHONY: clean-all
clean-all: clean  ## Remove output, venv, and all caches
	rm -rf $(VENV) .pytest_cache
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

.PHONY: help
help:  ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*##' $(MAKEFILE_LIST) \
	  | awk 'BEGIN {FS = ":.*##"}; {printf "  %-12s %s\n", $$1, $$2}'
