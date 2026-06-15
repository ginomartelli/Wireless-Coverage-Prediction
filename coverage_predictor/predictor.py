"""
Public inference API for LoRaWAN coverage prediction.

The underlying model is loaded once at import time.
To swap the model type, change the implementation in ``models.py``.
"""
import os
import sys

# ── Configuration ──
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config_loader import config  # noqa: E402

from models import ExtraTreesModel  # noqa: E402

INF_CFG = config["paths"]["inference"]
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ── Lazy model loader — model is loaded on first predict() call ──
#     This allows tests to import predictor without requiring the model.pkl
#     file to exist at import time.
_MODEL: ExtraTreesModel | None = None
_MODEL_LOADED: bool = False


def _ensure_model() -> ExtraTreesModel:
    """Return the singleton model, loading it on the first call."""
    global _MODEL, _MODEL_LOADED
    if not _MODEL_LOADED:
        _MODEL = ExtraTreesModel()
        model_path = os.path.join(BASE_DIR, INF_CFG["model_pkl"])
        _MODEL.load(model_path)
        _MODEL_LOADED = True
        print(f"Model loaded successfully from {model_path}")
    return _MODEL


def predict(
    lat: float,
    lon: float,
    gateway: str | None = None,
    frequency: float | None = None,
    spreading_factor: int | None = None,
) -> dict:
    """Predict RSSI with Out-of-Distribution safety.

    Returns a dict with keys:
        - ``rssi`` (float | None): predicted RSSI in dBm, or ``None`` when the
          location is out-of-distribution.
        - ``ood`` (bool): ``True`` when the prediction is unreliable because
          the query point lies outside the trained geographic domain.

    This function **never** raises — any exception raised by the underlying
    model, terrain loader, or KNN engine is caught and reported as OOD.

    Args:
        lat: Latitude of the location.
        lon: Longitude of the location.
        gateway: Gateway ID. Auto-selected if ``None``.
        frequency: LoRa centre frequency in Hz (default from ``config.yaml``).
        spreading_factor: LoRa spreading factor (default from ``config.yaml``).

    Returns:
        A dict ``{"rssi": ..., "ood": ...}``.
    """
    try:
        model = _ensure_model()
        rssi = model.predict(
            lat=lat,
            lon=lon,
            gateway=gateway,
            frequency=frequency,
            spreading_factor=spreading_factor,
        )
        return {"rssi": rssi, "ood": False}
    except Exception:
        return {"rssi": None, "ood": True}