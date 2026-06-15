# LoRaWAN Wireless Coverage Prediction

> **A production-grade ML system for predicting LoRaWAN Received Signal Strength (RSSI) across any geographic location.**  
> Achieves **R² = 0.9285 ± 0.0065** with **MAE = 1.93 dBm** — built for interactive coverage mapping, network planning, and real-time inference.

[![Python](https://img.shields.io/badge/python-3.12+-blue.svg)]()
[![Model](https://img.shields.io/badge/model-Extra%20Trees-green.svg)]()
[![R²](https://img.shields.io/badge/R%C2%B2-0.9285-brightgreen)]()
[![MAE](https://img.shields.io/badge/MAE-1.93%20dBm-yellow)]()
[![CI](https://img.shields.io/badge/CI-pytest%20%7C%20ruff-success)]()

---

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Key Features](#key-features)
- [🚀 Quick Start](#-quick-start)
- [⚙️ Configuration System](#️-configuration-system)
- [🏗️ Modular System Architecture](#️-modular-system-architecture)
  - [1. Data Ingestion & API Layer (`src/api/`)](#1-data-ingestion--api-layer-srcapi)
  - [2. Processing & Engineering Layer (`src/processing/`)](#2-processing--engineering-layer-srcprocessing)
  - [3. Training & ML Layer (`src/ml/`)](#3-training--ml-layer-srcml)
  - [4. Standalone Inference Engine (`coverage_predictor/`)](#4-standalone-inference-engine-coverage_predictor)
- [🔮 Inference API Reference](#-inference-api-reference)
  - [`predict()`](#predict)
  - [Out-of-Distribution (OOD) Detection](#out-of-distribution-ood-detection)
  - [Feature Generation Pipeline](#feature-generation-pipeline)
- [🏋️ Training Pipeline](#️-training-pipeline)
  - [Data Sources & Cleaning](#data-sources--cleaning)
  - [Feature Engineering](#feature-engineering)
  - [Model Training & Cross-Validation](#model-training--cross-validation)
- [🐳 Docker Deployment](#-docker-deployment)
  - [Inference Image](#inference-image)
  - [Training Image](#training-image)
  - [Building & Running](#building--running)
- [🧪 Testing](#-testing)
  - [Running Tests](#running-tests)
  - [Test Coverage](#test-coverage)
- [🔄 CI/CD Pipeline](#-cicd-pipeline)
- [🗺️ Adaptability Guide (Scaling to Other Regions)](#️-adaptability-guide-scaling-to-other-regions)
- [📁 Complete Project Tree](#-complete-project-tree)

---

## Architecture Overview

This repository features a **fully decoupled architecture** consisting of a complete **training pipeline** and a **standalone inference engine**.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        TRAINING PIPELINE (src/)                         │
│                                                                         │
│  ChirpStack API  ──►  Fetch (api/)  ──►  Parse  ──►  Clean  ──►        │
│       │                                                                │
│       ▼                                                                │
│  Feature Engineering (processing/)  ──►  Train (ml/)  ──►  model.pkl   │
│       │                                                                │
│       └──►  Reference Points (build_reference_dataset.py)              │
│       └──►  Gateways Registry (build_gateways_dataset.py)              │
└─────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      INFERENCE ENGINE (coverage_predictor/)              │
│                                                                         │
│  model.pkl  +  gateways.csv  +  reference_points.csv  +  Terrain DEMs   │
│                              │                                          │
│                              ▼                                          │
│  user calls  predict(lat, lon)  ──►  Feature Builder  ──►  Model  ──►  │
│                              │                                          │
│                              ▼                                          │
│              {"rssi": -108.7, "ood": False}                             │
└─────────────────────────────────────────────────────────────────────────┘
```

| Component | Directory | Purpose |
|-----------|-----------|---------|
| **Training Pipeline** | `src/` | Data fetching (ChirpStack API), cleaning, feature engineering, cross-validation, model serialization |
| **Inference Engine** | `coverage_predictor/` | Lightweight, importable module — loads a pre-trained model and geospatial assets to predict RSSI at arbitrary lat/lon |
| **Configuration** | `config.yaml` + `config_loader.py` | Centralized YAML configuration for all paths, radio params, KNN hyperparameters, antenna heights |
| **Tests** | `tests/` | Pytest suite covering valid predictions, OOD detection, and terrain queries |
| **Docker** | `Dockerfile` | Multi-stage build: `inference` (minimal), `training` (full), `builder` (intermediate) |
| **CI** | `.github/workflows/ci.yml` | Automated linting (ruff) + testing (pytest) on push/PR |

---

## Key Features

### 🔮 Out-of-Distribution (OOD) Detection
Predictions for locations far outside the training region (e.g., Paris, New York) automatically return `{"rssi": None, "ood": True}` instead of producing invalid results. The OOD check uses a **500 km threshold** from the nearest reference point.

### ⚙️ Centralized Configuration (`config.yaml`)
All file paths, radio parameters, KNN hyperparameters, antenna heights, and inference thresholds are externalized into a single `config.yaml` file. This means adapting the system to a new region often requires **editing only one file**.

### 🧩 Abstract Model Interface (`models.py`)
The inference engine uses an abstract `BaseModel` class. Currently implemented with `ExtraTreesModel`, but you can swap the model type by implementing a new subclass without changing the predictor.

### 🐌 Lazy Model Loading
The model is loaded from its `.pkl` file **on the first `predict()` call**, not at import time. This allows tests to import the predictor without requiring the model file to exist.

### 📦 Multi-Stage Docker Build
Three build stages:
- **`builder`** — compiles all Python dependencies (GDAL, GEOS, PROJ)
- **`inference`** — minimal image (~500 MB) for production prediction calls
- **`training`** — full environment for running data fetching + model training

### ✅ Comprehensive Test Suite
5 pytest tests covering valid predictions, OOD detection (Paris, New York), and terrain elevation lookups. Tests gracefully skip when model files are absent.

### 🔄 CI/CD Pipeline
GitHub Actions workflow that runs `ruff check` and `pytest tests/` on every push to `main`/`develop` and every PR to `main`.

### 🗺️ Gateway Auto-Selection & Fallback
When no gateway ID is provided, the nearest gateway is automatically selected. Unknown gateways trigger a graceful fallback using the closest known gateway's metadata, with a `gateway_unknown` feature flag to inform the model.

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.12+**
- **Geospatial raster files** (DEM `*.tif`, land-use `*.geojson`) placed under `coverage_predictor/data/terrain/`
- For training: **ChirpStack API credentials**

### 1. Clone the repository

```bash
git clone https://github.com/ginomartelli/Wireless-Coverage-Prediction.git
cd Wireless-Coverage-Prediction
```

### 2. Set up a virtual environment

```bash
python -m venv .venv
# Linux/macOS
source .venv/bin/activate
# Windows
.venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment (training only)

Copy `.env.example` to `.env` and fill in your ChirpStack credentials:

```bash
cp .env.example .env
```

```ini
BASE_URL=https://your-chirpstack-instance.com
EMAIL=your-email@example.com
PASSWORD=your-password
EMAIL2=your-second-email@example.com
PASSWORD2=your-second-password
```

### 5. Mount geospatial data

Place the following files under `coverage_predictor/data/terrain/`:

```
coverage_predictor/data/terrain/
├── dem1.tif            # SRTM DEM — Da Nang region (lat < 16.71)
├── dem2.tif            # SRTM DEM — Hai Phong region (lat ≥ 16.71)
├── landuse.geojson     # OSM land-use polygons — Da Nang
└── landuse2.geojson    # OSM land-use polygons — Hai Phong
```

> **Note:** These files are **not** included in the repository due to their large size. They must be downloaded separately (see [Adaptability Guide](#️-adaptability-guide-scaling-to-other-regions)).

### 6. Quick inference test

```python
from coverage_predictor.predictor import predict

result = predict(
    lat=16.0735,
    lon=108.1512,
)
if result["rssi"] is not None:
    print(f"Predicted RSSI: {result['rssi']:.1f} dBm")
print(f"OOD: {result['ood']}")
# Output:
# Predicted RSSI: -108.7 dBm
# OOD: False
```

### 7. Run the training pipeline

```bash
cd src
python main.py
```

The entry point `src/main.py` controls which stages run via boolean flags at the top of the file:

```python
FORCE_FETCH = False    # Force re-download from API
ADD_FEATURES = False   # Add basic features to dataset
TRAIN = True           # Train the model
SHOW_PLOTS = False     # Display error maps
PREDICT = False        # Run predictions on the training set
BUILD_REF = False      # Build reference dataset
BUILD_GW = False       # Build gateways dataset
```

---

## ⚙️ Configuration System

### `config.yaml` — Centralized Configuration

All configuration is externalized to `config.yaml` at the project root. The `config_loader.py` module loads it once (singleton pattern) and makes it available to all submodules.

```yaml
paths:
  inference:              # Paths used by coverage_predictor/
    gateways_csv: "./data/gateways.csv"
    reference_csv: "./data/reference_points.csv"
    model_pkl: "model/extra_trees_model.pkl"
    terrain_dir: "./data/terrain"
    dem1_tif: "dem1.tif"
    dem2_tif: "dem2.tif"
    landuse_geojson: "landuse.geojson"
    landuse2_geojson: "landuse2.geojson"

  training:               # Paths used by src/
    devices_history_csv: "../data/processed/devices_history_full.csv"
    devices_history_1_csv: "../data/processed/devices_history_1.csv"
    devices_history_2_csv: "../data/processed/devices_history_2.csv"
    dem_tif: "../data/terrain/dem.tif"
    dem2_tif: "../data/terrain/dem2.tif"
    landuse_geojson: "../data/terrain/landuse.geojson"
    landuse2_geojson: "../data/terrain/landuse2.geojson"
    model_output_dir: "ml/models"
    model_filename_template: "{model_type}_model_{date}.pkl"

radio:                    # LoRa radio parameters
  default_frequency: 922200000           # Hz
  default_spreading_factor: 7            # LoRa SF

knn:                      # KNN algorithm hyperparameters
  min_distance: 0.1                      # metres
  k: 9                                   # final neighbours
  k_search: 11                           # query candidates
  gw_distance_weight: 1.1                # gateway-distance penalty

inference:                # Engine behaviour
  closest_point_threshold_m: 30         # return RSSI directly if nearest ref ≤ 30 m
  out_of_range_rssi: -120.0              # RSSI when point is beyond gateway range

antenna:                  # Hardware heights
  gateway_height_m: 15
  device_height_m: 1.5

path_profile:             # Path-profile sampling
  step_meters: 30                        # interval along gateway–device path
```

### `config_loader.py` — How it Works

The configuration loader walks up the directory tree (up to 5 levels) from `config_loader.py` to find `config.yaml`. This means you can import it from any subdirectory:

```python
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config_loader import config

print(config["radio"]["default_frequency"])  # 922200000
```

You can also override the config path via the `CONFIG_PATH` environment variable.

### `.env` — Sensitive Credentials

| Variable | Required | Description |
|----------|----------|-------------|
| `BASE_URL` | ✅ | ChirpStack API base URL |
| `EMAIL` | ✅ | ChirpStack login email (Account 1 — Da Nang) |
| `PASSWORD` | ✅ | ChirpStack login password (Account 1) |
| `EMAIL2` | ✅ | ChirpStack login email (Account 2 — Hai Phong) |
| `PASSWORD2` | ✅ | ChirpStack login password (Account 2) |

---

## 🏗️ Modular System Architecture

### 1. Data Ingestion & API Layer (`src/api/`)

| File | Purpose |
|------|---------|
| `client.py` | JWT-based authentication with ChirpStack. Supports two accounts for cross-regional data. Exports `login()`, `get_headers()`, and `BASE_URL`. |
| `fetch_data.py` | Two main functions: `fetch_latest_devices()` (real-time status) and `fetch_device_history()` (historical data for a named device). |

**Authentication flow:**

```python
token = login(type=1)           # Account 1: Da Nang
headers = get_headers(token)
response = requests.post(url, headers=headers, json=payload)
```

### 2. Processing & Engineering Layer (`src/processing/`)

| File | Purpose |
|------|---------|
| `parser.py` | Converts raw API JSON to structured DataFrames. Parses device info, GNSS coordinates, LoRa modulation parameters, and gateway RX info. Includes `fix_gps()` to correct out-of-range coordinates. |
| `cleaning.py` | Removes invalid GPS (0,0) and surgically removes known outlier measurements (physically implausible RSSI at specific coordinates). |
| `features.py` | Computes KNN features (`add_closest_point_features`) using per-gateway KDTrees with distance-weighted scores. Implements the same KNN logic used during inference. |
| `terrain.py` | Raster I/O for DEMs (Digital Elevation Models) and land-use GeoJSON. Computes elevation, slope, roughness, Fresnel zone clearance, obstruction ratio, and terrain type ratios along the gateway–device path. |

**Key functions in `terrain.py`:**

- `get_elevation(lat, lon)` — reads from `dem1.tif` (Da Nang) or `dem2.tif` (Hai Phong) based on latitude
- `get_terrain_type(lat, lon)` — spatial query against land-use polygons
- `get_path_features(...)` — full path-profile analysis: samples terrain every 30 m, computes Fresnel zones and obstruction
- `add_terrain_features(df)` — batch processing for the training pipeline

### 3. Training & ML Layer (`src/ml/`)

| File | Purpose |
|------|---------|
| `pipeline.py` | Defines the sklearn `Pipeline` with `ColumnTransformer` (StandardScaler + OneHotEncoder) and the ExtraTreesRegressor. Lists all 30+ numeric and categorical features. |
| `train.py` | Implements **5-fold shuffled cross-validation** with strict data leakage prevention (reference dataset computed per fold). Trains the final model on the full dataset and saves it with a date-stamped filename. |
| `predict.py` | Batch prediction for the training set. Loads a saved model and applies the full feature pipeline. |

**Numeric features used by the model (30 features):**

| Category | Features |
|----------|----------|
| Radio | `frequency`, `spreading_factor` |
| Geometry | `distance_3d`, `log_distance_3d`, `delta_lat`, `delta_lon`, `angle`, `elevation_angle` |
| KNN | `rssi_closest_point`, `distance_closest_point`, `closest_to_gw_distance`, `neighbor_rssi_mean`, `neighbor_rssi_weighted_mean`, `neighbor_rssi_std`, `neighbor_distance_mean`, `neighbor_gw_distance_mean` |
| Elevation | `elevation`, `gw_elevation`, `delta_elevation` |
| Terrain | `slope`, `roughness`, `terrain_mean`, `terrain_std`, `terrain_min`, `terrain_max`, `terrain_range` |
| Path | `max_obstruction`, `fresnel_obstruction_ratio`, `min_fresnel_clearance`, `mean_fresnel_clearance`, `residential_ratio` |
| Gateway | `gateway_unknown` |

**Categorical features:** `gateway`

**Best model parameters:**

```python
ExtraTreesRegressor(
    n_estimators=650,
    max_depth=18,
    min_samples_split=10,
    max_features=0.7,
    random_state=42,
    n_jobs=-1
)
```

**Performance metrics (5-fold CV):**

| Metric | Value |
|--------|-------|
| **R²** | **0.9285 ± 0.0065** |
| **MAE** | **1.93 dBm** |
| **RMSE** | **2.92 dBm** |

### 4. Standalone Inference Engine (`coverage_predictor/`)

A dependency-minimized module designed for production deployment. All geospatial assets (CSVs, DEMs, model) are loaded once at import time.

| File | Purpose |
|------|---------|
| `predictor.py` | **Public API** — `predict(lat, lon)` returns `{"rssi": float, "ood": bool}`. Implements lazy model loading and OOD safety (never raises). |
| `models.py` | **Abstract model interface** — `BaseModel` ABC with `ExtraTreesModel` implementation. Makes the model swappable. |
| `feature_builder.py` | **On-the-fly feature construction** — gateway selection (auto or specified), geometry, terrain, and KNN features for a single lat/lon point. |
| `neighbor_features.py` | **KDTree spatial queries** — builds per-gateway KDTrees from reference points. `closest_reference_point()` and `compute_neighbor_features()`. |
| `terrain.py` | **Raster I/O** — same terrain logic as training but optimized for single-point queries. |

**Data files:**

| File | Format | Description |
|------|--------|-------------|
| `data/gateways.csv` | CSV | Gateway registry: ID, lat, lon, elevation, range |
| `data/reference_points.csv` | CSV | Historical measurements: lat, lon, gateway, RSSI, distance |
| `data/terrain/dem1.tif` | GeoTIFF | SRTM DEM — Da Nang region |
| `data/terrain/dem2.tif` | GeoTIFF | SRTM DEM — Hai Phong region |
| `data/terrain/landuse.geojson` | GeoJSON | OSM land-use polygons — Da Nang |
| `data/terrain/landuse2.geojson` | GeoJSON | OSM land-use polygons — Hai Phong |
| `model/extra_trees_model.pkl` | Pickle | Trained sklearn pipeline |

---

## 🔮 Inference API Reference

### `predict()`

```python
from coverage_predictor.predictor import predict

result = predict(
    lat: float,                          # Latitude of the query point
    lon: float,                          # Longitude of the query point
    gateway: str | None = None,          # Gateway ID (auto-selected if None)
    frequency: float | None = None,      # LoRa frequency in Hz (default from config)
    spreading_factor: int | None = None, # LoRa spreading factor (default from config)
) -> dict                                # {"rssi": float | None, "ood": bool}
```

**Return values:**

| Scenario | `result` |
|----------|----------|
| Valid prediction (Da Nang) | `{"rssi": -108.7, "ood": False}` |
| Out-of-Distribution (Paris) | `{"rssi": None, "ood": True}` |
| Beyond gateway range | `{"rssi": -120.0, "ood": False}` |
| Very close to reference point (≤ 30 m) | `{"rssi": -87.0, "ood": False}` (raw RSSI from nearest reference) |

### Out-of-Distribution (OOD) Detection

The OOD mechanism works in **two layers**:

1. **KNN distance check** (in `feature_builder.py`): If the nearest reference point is > 500 km away, a `ValueError` is raised.
2. **Catch-all exception handler** (in `predictor.py`): Any exception during prediction (FileNotFoundError, raster I/O errors, etc.) is caught and returns `{"rssi": None, "ood": True}`.

This guarantees that `predict()` **never raises an exception** — it always returns a dict.

### Feature Generation Pipeline

When `predict()` is called, the following features are constructed in order:

```
predict(lat, lon)
  │
  ├── 1. Find nearest reference point (KDTree query)
  │     └── If distance > 500 km → OOD (ValueError)
  │     └── If distance ≤ 30 m → return reference RSSI directly
  │
  ├── 2. Gateway selection
  │     └── If gateway=None → use the nearest reference's gateway
  │     └── If gateway unknown → fallback to closest known gateway + flag
  │     └── If distance > gateway range → return -120.0 dBm
  │
  ├── 3. Geometry features
  │     └── distance_3d, log_distance_3d, delta_lat, delta_lon,
  │         angle, elevation_angle
  │
  ├── 4. Terrain features (from DEM + land-use)
  │     └── elevation, slope, roughness
  │     └── Path profile: terrain_mean, terrain_std, terrain_min/max/range
  │         max_obstruction, fresnel_obstruction_ratio,
  │         min_fresnel_clearance, mean_fresnel_clearance,
  │         residential_ratio
  │
  ├── 5. KNN features (from reference points)
  │     └── rssi_closest_point, distance_closest_point,
  │         closest_to_gw_distance, neighbor_rssi_mean,
  │         neighbor_rssi_weighted_mean (exponential decay),
  │         neighbor_rssi_std, neighbor_distance_mean,
  │         neighbor_gw_distance_mean
  │
  ├── 6. Feature DataFrame assembled (30+ columns)
  │
  └── 7. ExtraTreesRegressor predicts RSSI in dBm
```

---

## 🏋️ Training Pipeline

### Data Sources & Cleaning

**Data sources:** Real-world LoRaWAN measurements from Da Nang and Hai Phong, Vietnam, collected via the ChirpStack API.

**Cleaning steps:**
1. Remove invalid GPS coordinates (`lat=0, lon=0`)
2. Remove surgically identified outliers (physically implausible RSSI at specific coordinates matching known bad measurements)
3. Shuffled duplicate measurements are **preserved** to capture local signal variance

### Feature Engineering

Features are added in two stages:

**Stage 1 — Basic features (`features.py`):**
- Distance (Haversine), log-distance
- Delta lat/lon, angle

**Stage 2 — Terrain features (`terrain.py`):**
- Elevation (from DEM rasters)
- Slope, roughness
- Path-profile analysis (Fresnel zones, obstruction)
- Land-use ratios (residential, forest, water)

**Stage 3 — KNN features (`features.py`):**
- Per-gateway KDTree queries
- Distance-weighted scores with gateway-distance penalty
- Exponential decay weighting (`w = exp(-dist / 30)`)

### Model Training & Cross-Validation

The training process (`src/ml/train.py`) implements **strictly decoupled** 5-fold cross-validation:

```
For each fold:
  1. Split data → train_fold, test_fold
  2. Compute KNN features for train_fold using train_fold as reference
  3. Compute KNN features for test_fold using train_fold as reference (NO LEAKAGE!)
  4. Fit pipeline on train_fold
  5. Predict on test_fold
  6. Record R², MAE, RMSE

After all folds:
  7. Train final model on full dataset
  8. Save model to ml/models/extra_trees_model_{date}.pkl
```

The preprocessing pipeline includes:
- `SimpleImputer(strategy="median")` for numeric features
- `StandardScaler` for numeric features
- `SimpleImputer(strategy="most_frequent")` for categorical features
- `OneHotEncoder(handle_unknown="ignore")` for gateway IDs

---

## 🐳 Docker Deployment

The project includes a **multi-stage Dockerfile** with three build targets:

### Inference Image

Minimal image (~500 MB) containing only the inference engine. Designed for production deployment where predictions are queried via Python API.

```
docker build --target inference -t wireless-coverage-inference:latest .
```

**Mount requirements:**

Only the terrain directory needs to be mounted — the CSV files (`gateways.csv`, `reference_points.csv`) and the model (`extra_trees_model.pkl`) are baked into the image via `COPY coverage_predictor/ .`.

```bash
-v /host/path/to/terrain:/app/coverage_predictor/data/terrain
```

### Training Image

Full build environment including API client, processing pipeline, and model training.

```
docker build --target training -t wireless-coverage-training:latest .
```

**Mount requirements:**
- `/app/data/processed/` — historical device measurements
- `/app/data/terrain/` — DEM and land-use files
- `/app/data/raw/` — raw API exports (optional)

### Builder Stage

Intermediate stage used to compile all Python dependencies (GDAL, GEOS, PROJ). Never run directly.

### Building & Running

```bash
# Build the inference image
docker build --target inference -t wireless-coverage-inference:test .

# Run a prediction inside the container (with terrain data mounted)
docker run --rm -v /path/to/terrain:/app/coverage_predictor/data/terrain \
  wireless-coverage-inference:test \
  python -c "
from predictor import predict
print(predict(16.0735, 108.1512))
"
```

---

## 🧪 Testing

### Running Tests

```bash
# Run all tests with verbose output
pytest tests/ -v --tb=short
```

### Test Coverage

| Test | File | Description |
|------|------|-------------|
| `test_predictor_valid` | `tests/test_predictor.py` | Valid Vietnam coordinate → finite RSSI, `ood=False` |
| `test_predictor_ood_paris` | `tests/test_predictor.py` | Paris → `ood=True`, `rssi=None` (no model file needed) |
| `test_predictor_ood_new_york` | `tests/test_predictor.py` | New York → `ood=True`, `rssi=None` (no model file needed) |
| `test_terrain_elevation_valid` | `tests/test_predictor.py` | Elevation lookup returns a realistic value |
| `test_terrain_elevation_ood` | `tests/test_predictor.py` | Elevation outside DEM coverage returns `None` |

**Smart test skipping:** Tests that require model/DEM files are automatically skipped when those files are missing (e.g., in a fresh CI environment or before training).

```python
# Example: OOD tests pass WITHOUT any model/DEM files
def test_predictor_ood_paris():
    result = predict(lat=48.8566, lon=2.3522)
    assert result["ood"] is True
    assert result["rssi"] is None
```

---

## 🔄 CI/CD Pipeline

A GitHub Actions workflow (`.github/workflows/ci.yml`) runs on every push and pull request:

```yaml
jobs:
  lint:                     # ruff check
    runs-on: ubuntu-latest
    steps:
      - ruff check .

  test:                     # pytest (depends on lint passing)
    needs: lint
    runs-on: ubuntu-latest
    steps:
      - Install system deps: gdal-bin, libgdal-dev, libgeos-dev, libproj-dev
      - pip install -r requirements.txt
      - pytest tests/ -v --tb=short
```

**CI pipeline features:**
- Linting with `ruff` before testing
- System dependency installation (GDAL, GEOS, PROJ) for geospatial package compilation
- Tests gracefully skip when model/DEM files are absent

---

## 🗺️ Adaptability Guide (Scaling to Other Regions)

To adapt this system to a new geographic region:

### 1. Acquire DEM (Digital Elevation Model)

Download SRTM tiles (1 arc-second, ~30 m resolution) from:
- [USGS EarthExplorer](https://earthexplorer.usgs.gov/)
- [OpenTopography](https://opentopography.org/)

Place `.tif` files in `coverage_predictor/data/terrain/` and update `config.yaml`:
```yaml
paths:
  inference:
    dem1_tif: "your_region_dem.tif"
```

### 2. Download OSM Land-Use Data

Run `src/download_osm.py` with your new bounding box:

```python
from shapely.geometry import Polygon
polygon = Polygon([
    (lon_min, lat_min),
    (lon_max, lat_min),
    (lon_max, lat_max),
    (lon_min, lat_max)
])
gdf = ox.features_from_polygon(polygon, tags={"landuse": True, "natural": True})
gdf.to_file("../data/terrain/landuse.geojson")
```

### 3. Register Gateways

Update `data/gateways.csv` with local gateway coordinates, elevations, and ranges:
```csv
gateway,gw_lat,gw_lon,gw_elevation,range
your_gateway_id,16.07419,108.15262,14.0,876.36
```

### 4. Collect Reference Data

Run `python src/build_reference_dataset.py` to build `data/reference_points.csv` from your historical measurements.

### 5. Retrain the Model

Update `config.yaml` with your new paths, then:
```bash
cd src
python main.py
```
Set `TRAIN = True` in `main.py`.

### 6. Verify Inference

```python
from coverage_predictor.predictor import predict
result = predict(lat=your_lat, lon=your_lon)
print(result)  # {"rssi": -105.2, "ood": False}
```

---

## 📁 Complete Project Tree

```
Wireless-Coverage-Prediction/
│
├── README.md                        # This file
├── requirements.txt                 # Pinned Python dependencies
├── config.yaml                      # Centralized configuration
├── config_loader.py                 # YAML config loader (singleton)
├── pyproject.toml                   # Project metadata + build config
├── .env.example                     # Template for ChirpStack credentials
├── .dockerignore                    # Files excluded from Docker context
├── Dockerfile                       # Multi-stage Docker build
│
├── coverage_predictor/              # Standalone inference engine
│   ├── predictor.py                 # Public API: predict(lat, lon) -> dict
│   ├── models.py                    # Abstract BaseModel + ExtraTreesModel
│   ├── feature_builder.py           # Single-point feature construction
│   ├── neighbor_features.py         # KDTree spatial search
│   ├── terrain.py                   # Raster I/O (DEM, land-use)
│   ├── predicted_coverage.csv       # Sample coverage output (optional)
│   │
│   ├── data/
│   │   ├── gateways.csv             # Gateway registry
│   │   ├── reference_points.csv     # Historical measurements
│   │   └── terrain/                 # Geospatial rasters (gitignored)
│   │       ├── dem1.tif
│   │       ├── dem2.tif
│   │       ├── landuse.geojson
│   │       └── landuse2.geojson
│   │
│   └── model/
│       └── extra_trees_model.pkl    # Trained sklearn pipeline
│
├── src/                             # Training pipeline
│   ├── main.py                      # Entry point (flags-controlled)
│   ├── download_osm.py              # OSM land-use downloader
│   ├── build_gateways_dataset.py    # Build gateways.csv from training data
│   ├── build_reference_dataset.py   # Build reference_points.csv
│   │
│   ├── api/
│   │   ├── client.py                # JWT auth + ChirpStack client
│   │   └── fetch_data.py            # Fetch device history/latest
│   │
│   ├── processing/
│   │   ├── parser.py                # Raw JSON -> DataFrame parser
│   │   ├── cleaning.py              # Outlier removal
│   │   ├── features.py              # KNN feature engineering
│   │   └── terrain.py               # DEM + terrain features (batch)
│   │
│   └── ml/
│       ├── pipeline.py              # sklearn Pipeline definition
│       ├── train.py                 # 5-fold CV + final training
│       ├── predict.py               # Batch prediction
│       └── models/
│           └── extra_trees_model.pkl # Trained model (or symlink)
│
├── data/                            # Raw & processed datasets
│   ├── raw/                         # Raw API exports
│   ├── processed/                   # Cleaned CSV files
│   ├── backup/                      # Backup datasets
│   └── terrain/                     # DEM/land-use for training
│
├── tests/
│   ├── conftest.py                  # Pytest fixtures (if any)
│   └── test_predictor.py            # 5 tests: valid, OOD, terrain
│
└── .github/workflows/
    └── ci.yml                       # GitHub Actions: ruff + pytest
```
