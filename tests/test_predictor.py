"""
Unit tests for the coverage predictor engine.

Run with::

    pytest tests/ -v --tb=short

Tests that require model / terrain data are automatically skipped when the
corresponding files are missing (e.g. in a fresh CI environment).
"""

import os
import sys
from pathlib import Path

import pytest

# ── Path setup (ensure config_loader + coverage_predictor are importable) ──
PROJECT_ROOT = Path(__file__).resolve().parent.parent
COVERAGE_PREDICTOR = PROJECT_ROOT / "coverage_predictor"
for p in [str(PROJECT_ROOT), str(COVERAGE_PREDICTOR)]:
    if p not in sys.path:
        sys.path.insert(0, p)


# ── Data availability checks ──
def _model_path() -> str:
    """Return the resolved path to the serialised model file."""
    from config_loader import config
    inf = config["paths"]["inference"]
    return str(COVERAGE_PREDICTOR / inf["model_pkl"])


def _dem_path() -> str:
    """Return the resolved path to the primary DEM file."""
    from config_loader import config
    inf = config["paths"]["inference"]
    return str(COVERAGE_PREDICTOR / inf["terrain_dir"] / inf["dem1_tif"])


_HAS_MODEL = os.path.isfile(_model_path())
_HAS_DEM = os.path.isfile(_dem_path())

skipif_no_model = pytest.mark.skipif(
    not _HAS_MODEL,
    reason=f"Model file not found at {_model_path()}",
)
skipif_no_dem = pytest.mark.skipif(
    not _HAS_DEM,
    reason=f"DEM file not found at {_dem_path()}",
)


# ============================================================================
# Test: valid prediction (Da Nang, Vietnam)
# ============================================================================

@skipif_no_model
@skipif_no_dem
def test_predictor_valid():
    """A standard Vietnam coordinate returns a finite RSSI and ood=False."""
    from predictor import predict

    result = predict(lat=16.0735, lon=108.1512)

    assert isinstance(result, dict), "predict() should return a dict"
    assert {"rssi", "ood"} <= result.keys(), "dict must contain 'rssi' and 'ood'"
    assert result["ood"] is False, "valid Vietnam coordinate should not be OOD"
    assert result["rssi"] is not None, "rssi should be a float, not None"
    assert isinstance(result["rssi"], float), f"expected float, got {type(result['rssi'])}"
    # Physically plausible RSSI range for LoRaWAN
    assert -140 <= result["rssi"] <= -30, (
        f"RSSI {result['rssi']:.1f} dBm outside physically plausible range [-140, -30]"
    )


# ============================================================================
# Test: OOD prediction (Paris, France)
# ============================================================================

def test_predictor_ood_paris():
    """A coordinate in Paris should return ood=True without crashing.

    This test does NOT require model / DEM files — the OOD handler in
    predict() catches the FileNotFoundError raised by lazy model loading.
    """
    from predictor import predict

    result = predict(lat=48.8566, lon=2.3522)

    assert isinstance(result, dict), "predict() should return a dict"
    assert result["ood"] is True, "Paris should be detected as OOD"
    assert result["rssi"] is None, "rssi should be None for OOD locations"


# ============================================================================
# Test: OOD prediction (New York, USA)
# ============================================================================

def test_predictor_ood_new_york():
    """A coordinate in New York should return ood=True without crashing."""
    from predictor import predict

    result = predict(lat=40.7128, lon=-74.0060)

    assert isinstance(result, dict), "predict() should return a dict"
    assert result["ood"] is True, "New York should be detected as OOD"
    assert result["rssi"] is None, "rssi should be None for OOD locations"





# ============================================================================
# Test: terrain elevation for valid / invalid locations
# ============================================================================

@skipif_no_dem
def test_terrain_elevation_valid():
    """Elevation lookup returns a finite float for a known DEM location."""
    from terrain import get_elevation

    # Da Nang, Vietnam (should be covered by dem1.tif)
    elev = get_elevation(lat=16.0735, lon=108.1512)

    assert elev is not None, "elevation should not be None for a covered location"
    assert isinstance(elev, float), f"expected float, got {type(elev)}"
    assert 0 <= elev <= 200, f"elevation {elev:.1f} m seems unrealistic for Da Nang"


@skipif_no_dem
def test_terrain_elevation_ood():
    """Elevation lookup returns None for a location outside DEM coverage."""
    from terrain import get_elevation

    elev = get_elevation(lat=48.8566, lon=2.3522)

    assert elev is None, "elevation should be None for uncovered locations"
