"""
Abstract model interface for the Wireless Coverage Prediction inference engine.

Usage:
    from models import ExtraTreesModel

    model = ExtraTreesModel()
    model.load("model/extra_trees_model.pkl")
    rssi = model.predict(lat=16.0735, lon=108.1512)
"""

from __future__ import annotations

import os
import sys
from abc import ABC, abstractmethod
from numbers import Number
from typing import Any

import numpy as np
import pandas as pd
from joblib import load

# ── Configuration ──
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config_loader import config  # noqa: E402


# ============================================================================
# Abstract interface
# ============================================================================

class BaseModel(ABC):
    """Abstract base class for coverage prediction models.

    Subclasses must implement ``load()`` and ``predict()``.
    """

    @abstractmethod
    def load(self, path: str) -> None:
        """Deserialize a trained model from ``path``."""
        ...

    @abstractmethod
    def predict(
        self,
        lat: float,
        lon: float,
        gateway: str | None = None,
        frequency: float | None = None,
        spreading_factor: int | None = None,
    ) -> float:
        """Return predicted RSSI in dBm for a single geographic point."""
        ...

    def __repr__(self) -> str:
        return f"{type(self).__name__}()"


# ============================================================================
# Extra Trees implementation
# ============================================================================

class ExtraTreesModel(BaseModel):
    """Concrete Extra-Trees regressor wrapping the full inference pipeline.

    The pipeline consists of:
    1. ``feature_builder.build_features()``  — geometry, terrain, KNN features
    2. sklearn ``Pipeline`` (preprocessor → ExtraTreesRegressor)
    """

    def __init__(self) -> None:
        self._pipeline: Any = None  # sklearn Pipeline or compatible object
        self._loaded_path: str | None = None

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------

    def load(self, path: str) -> None:
        """Load a trained sklearn pipeline from a ``.pkl`` file."""
        from joblib import load as _joblib_load

        self._pipeline = _joblib_load(path)
        self._loaded_path = path

    # ------------------------------------------------------------------
    # Public prediction API
    # ------------------------------------------------------------------

    def predict(
        self,
        lat: float,
        lon: float,
        gateway: str | None = None,
        frequency: float | None = None,
        spreading_factor: int | None = None,
    ) -> float:
        """Return predicted RSSI in dBm.

        Arguments are forwarded to ``feature_builder.build_features()``.
        """
        if self._pipeline is None:
            raise RuntimeError(
                "Model not loaded. Call .load(path) first."
            )

        from feature_builder import build_features  # noqa: C0415

        # Apply defaults from config when caller omits optional params
        RADIO = config["radio"]
        if frequency is None:
            frequency = RADIO["default_frequency"]
        if spreading_factor is None:
            spreading_factor = RADIO["default_spreading_factor"]

        features = build_features(
            lat=lat,
            lon=lon,
            gateway=gateway,
            frequency=frequency,
            spreading_factor=spreading_factor,
        )

        # Shortcut: ``build_features`` returns a raw float when the point
        # is within the closest-point threshold or out of range.
        if isinstance(features, Number):
            return float(features)

        return float(self._pipeline.predict(features)[0])
