"""
Lightweight configuration loader for Wireless Coverage Prediction.

Usage (from any module inside coverage_predictor/ or src/):

    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
    from config_loader import config

    print(config["paths"]["inference"]["gateways_csv"])
    print(config["radio"]["default_frequency"])
"""

import os
import yaml

_CONFIG: dict | None = None
_CONFIG_PATH: str | None = None


def _locate_config() -> str:
    """Find ``config.yaml`` by walking up from this file's directory.

    Raises ``FileNotFoundError`` if no ``config.yaml`` is found within 5
    parent levels.
    """
    start = os.path.dirname(os.path.abspath(__file__))
    for _ in range(5):
        candidate = os.path.join(start, "config.yaml")
        if os.path.isfile(candidate):
            return candidate
        parent = os.path.dirname(start)
        if parent == start:
            break
        start = parent
    raise FileNotFoundError(
        "config.yaml not found. "
        "Ensure the file exists at the project root and that "
        "config_loader.py is in the same directory (or the CWD)."
    )


def load_config(force_reload: bool = False) -> dict:
    """Return the configuration dictionary, loading from YAML once (singleton)."""
    global _CONFIG, _CONFIG_PATH
    if _CONFIG is not None and not force_reload:
        return _CONFIG
    if _CONFIG_PATH is None:
        _CONFIG_PATH = os.environ.get("CONFIG_PATH") or _locate_config()
    with open(_CONFIG_PATH, "r", encoding="utf-8") as fh:
        _CONFIG = yaml.safe_load(fh)
    print(f"[config_loader] Loaded configuration from {_CONFIG_PATH}")
    return _CONFIG


# ── Module-level singleton — importers get this automatically ──
config: dict = load_config()
