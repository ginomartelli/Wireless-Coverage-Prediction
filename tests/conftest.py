"""
pytest configuration for Wireless Coverage Prediction tests.

Auto-discovers the project root so ``config_loader`` can be imported
from ``tests/`` without manual ``sys.path`` manipulation.
"""

import sys
from pathlib import Path

import pytest

# Ensure the project root is on sys.path so that config_loader & co. are
# importable from tests/.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture(scope="session")
def project_root() -> Path:
    """Return the absolute path to the project root."""
    return PROJECT_ROOT


@pytest.fixture(scope="session")
def coverage_predictor_root(project_root: Path) -> Path:
    """Return the absolute path to the ``coverage_predictor/`` module."""
    return project_root / "coverage_predictor"
