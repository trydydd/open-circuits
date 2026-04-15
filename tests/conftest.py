"""
Pytest fixtures for the Open Circuits integration test suite.

The `upstream_html` fixture downloads the real Kuphaldt HTML bundle once
per session (idempotent — skips if already present).  The `output_html`
fixture runs the overlay injection on that real HTML, also once per session.

Both fixtures are session-scoped so the expensive operations happen only once
regardless of how many individual tests run.
"""

import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent
PYTHON = sys.executable  # venv Python that is running pytest


def _run(script: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    result = subprocess.run(
        [PYTHON, str(script), *args],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )
    if check and result.returncode != 0:
        raise AssertionError(
            f"{script.name} exited {result.returncode}:\n"
            f"stdout: {result.stdout}\n"
            f"stderr: {result.stderr}"
        )
    return result


@pytest.fixture(scope="session")
def upstream_html() -> Path:
    """
    Ensure upstream/html/ is populated with the real Kuphaldt HTML.
    Downloads from ibiblio if not already present (idempotent).
    Returns the path to upstream/html/.
    """
    _run(REPO_ROOT / "build" / "download_source.py")
    html_dir = REPO_ROOT / "upstream" / "html"
    assert html_dir.is_dir(), "upstream/html/ missing after download"
    return html_dir


@pytest.fixture(scope="session")
def output_html(upstream_html: Path, tmp_path_factory: pytest.TempPathFactory) -> Path:
    """
    Run inject_overlay.py on the real upstream HTML.
    Returns the path to the injected output directory.
    """
    out_dir = tmp_path_factory.mktemp("output_html")
    _run(
        REPO_ROOT / "overlay" / "inject_overlay.py",
        str(upstream_html),
        str(out_dir),
    )
    return out_dir
