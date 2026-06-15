# LoRaWAN Wireless Coverage Prediction

> **A production-grade ML system for predicting LoRaWAN Received Signal Strength (RSSI) across any geographic location.**  
> Achieves **R² = 0.9285 ± 0.0065** with **MAE = 1.93 dBm** — built for interactive coverage mapping, network planning, and real-time inference.

[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)]()
[![Model](https://img.shields.io/badge/model-Extra%20Trees-green.svg)]()
[![R²](https://img.shields.io/badge/R%C2%B2-0.9285-brightgreen)]()
[![MAE](https://img.shields.io/badge/MAE-1.93%20dBm-yellow)]()

---

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [🚀 Quick Start](#-quick-start)
- [⚙️ Configuration & Environment Variables](#️-configuration--environment-variables)
- [🏗️ Modular System Architecture](#️-modular-system-architecture)
- [🏋️ Training & Data Pipeline (Vietnam Scope)](#️-training--data-pipeline-vietnam-scope)
- [🗺️ Adaptability Guide](#️-adaptability-guide-scaling-to-other-regions)
- [🧪 Acceptance Criteria & Verification](#-acceptance-criteria--verification)
- [Project Tree](#-project-tree)

---

## Architecture Overview

This repository features a **decoupled architecture** consisting of a full **training pipeline** and a **standalone inference engine**.

| Component | Directory | Purpose |
|-----------|-----------|---------|
| **Training Pipeline** | `src/` | Data fetching (ChirpStack API), cleaning, feature engineering, cross-validation, and model serialization. |
| **Inference Engine** | `coverage_predictor/` | Lightweight, importable module that loads a pre-trained model and geospatial assets to predict RSSI at arbitrary lat/lon. |

**Data flow:**

```
ChirpStack API  ──►  Fetch (src/api/)  ──►  Parse & Clean  ──►  Feature Engineering  ──►  Train (Extra Trees)
                                                                                              │
                                                                                              ▼
          Interactive Coverage Map  ◄──  predictor.predict(lat, lon)  ◄──  coverage_predictor/  ◄──  model.pkl
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Geospatial raster files (DEM `*.tif`, land-use `*.geojson`) placed under `coverage_predictor/data/terrain/`

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

### 4. Configure environment

Create a `.env` file at the **project root**:

```bash
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
├── dem.tif              # SRTM DEM — Da Nang region (lat < 16.71)
├── dem2.tif             # SRTM DEM — Hai Phong region (lat ≥ 16.71)
├── landuse.geojson      # OSM land-use polygons — Da Nang
└── landuse2.geojson     # OSM land-use polygons — Hai Phong
```

### 6. Run the training pipeline

```bash
cd src
python main.py
```

### 7. Run inference (standalone)

```python
from coverage_predictor.predictor import predict

rssi = predict(
    lat=16.0735,
    lon=108.1512,
    frequency=922200000,
    spreading_factor=7,
)
print(f"Predicted RSSI: {rssi:.1f} dBm")
```

---

## ⚙️ Configuration & Environment Variables

### `.env` variables

| Variable | Required | Description |
|----------|----------|-------------|
| `BASE_URL` | ✅ | ChirpStack API base URL. |
| `EMAIL` | ✅ | ChirpStack login email (Account 1 — Da Nang). |
| `PASSWORD` | ✅ | ChirpStack login password (Account 1). |
| `EMAIL2` | ✅ | ChirpStack login email (Account 2 — Hai Phong). |
| `PASSWORD2` | ✅ | ChirpStack login password (Account 2). |

### Read-only geospatial volumes

The inference engine expects these files at the paths below:

| Path | Format | Description |
|------------|--------|-------------|
| `coverage_predictor/data/terrain/dem.tif` | GeoTIFF | SRTM DEM (Da Nang: lat < 16.71). |
| `coverage_predictor/data/terrain/dem2.tif` | GeoTIFF | SRTM DEM (Hai Phong: lat ≥ 16.71). |
| `coverage_predictor/data/terrain/landuse.geojson` | GeoJSON | OSM land-use polygons (Da Nang). |
| `coverage_predictor/data/terrain/landuse2.geojson` | GeoJSON | OSM land-use polygons (Hai Phong). |

---

## 🏗️ Modular System Architecture

### 1. Data Ingestion & API Layer (`src/api/`)
Handles authentication via JWT and fetches device history/latest status from ChirpStack. Supports multi-account fetching for cross-regional data.

### 2. Processing & Engineering Layer (`src/processing/`)
- **Parser:** Converts raw API JSON to structured DataFrames.
- **Cleaning:** Removes invalid GPS coordinates (0,0) and physically implausible RSSI outliers.
- **Features:** Computes 3D geometry, terrain characteristics (slope, roughness), and Path-Profile features (Fresnel zone clearance).
- **Terrain:** Manages raster I/O for Digital Elevation Models (DEM).

### 3. Training & ML Layer (`src/ml/`)
- **Pipeline:** Sklearn pipeline including `ColumnTransformer`, `StandardScaler`, `OneHotEncoder`, and `ExtraTreesRegressor`.
- **Training:** Implements 5-fold shuffled cross-validation.
- **Reference Builder:** Generates the KDTree-based reference dataset for nearest-neighbor features.

### 4. Standalone Inference Engine (`coverage_predictor/`)
A dependency-minimized module for production deployment.
- **Predictor:** Public API for single-point RSSI prediction.
- **Feature Builder:** On-the-fly construction of geometry and terrain features.
- **Neighbor Features:** Efficient KDTree spatial queries for local interpolation.

---

## 🏋️ Training & Data Pipeline (Vietnam Scope)

### Data Sources & Outlier Removal
The model is trained on real-world measurements from Vietnam (Da Nang & Hai Phong). During preprocessing, **extreme outliers** (physically inconsistent RSSI vs Distance) were surgically removed based on coordinate-matching rules, while **shuffled duplicate measurements** were preserved to capture local signal variance.

### Training Data Split
The dataset is evaluated using a **5-fold shuffled cross-validation** strategy.
- **Leakage Prevention:** Nearest-neighbor features for the validation fold are computed exclusively from the training fold's reference data.

### Feature Engineering
Features are categorized into:
1. **Geometry:** `distance_3d`, `log_distance_3d`, `elevation_angle`, `delta_elevation`.
2. **Terrain:** `elevation`, `slope`, `roughness`, `residential_ratio`.
3. **Path Profile:** `terrain_mean/std/min/max`, `max_obstruction`, `fresnel_obstruction_ratio`.
4. **Nearest-Neighbor (KNN):** `neighbor_rssi_weighted_mean` (exponential decay), `rssi_closest_point`.

### Model Selection
**Extra Trees** was selected after benchmarking against RF, XGBoost, and HistGradientBoost. It provides superior variance reduction on geospatial features.

**Best Parameters:**
```python
ExtraTreesRegressor(
    n_estimators=650,
    max_depth=18,
    min_samples_split=10,
    max_features=0.7,
    random_state=42
)
```

### Performance Metrics (Verified)
| Metric | Value |
|--------|-------|
| **R²** | **0.9285 ± 0.0065** |
| **MAE** | **1.93 dBm** |
| **RMSE** | **2.92 dBm** |

---

## 🗺️ Adaptability Guide

To scale this model to other regions:

1. **Acquire DEM:** Download SRTM tiles (1 arc-second) and place in `data/terrain/`.
2. **Download OSM:** Run `src/download_osm.py` with your new bounding box.
3. **Registry Gateways:** Update `data/gateways.csv` with local gateway coordinates and heights.
4. **Build Reference:** Collect data and run `src/build_reference_dataset.py`.
5. **Retrain:** Execute `src/main.py`.

---

## 🧪 Acceptance Criteria & Verification

| # | Criterion | Verification |
|---|-----------|-------------|
| 1 | `predict()` returns finite float | Run `coverage_predictor/testing.py`. |
| 2 | R² ≥ 0.90 | Verified on 5-fold CV. |
| 3 | MAE ≤ 2.0 dBm | Verified on 5-fold CV. |
| 4 | No data leakage | Reference set strictly decoupled in `ml/train.py`. |
| 5 | Deterministic | Identical inputs yield identical outputs (stateless inference). |

---

## 📁 Project Tree

```
Wireless-Coverage-Prediction/
│
├── README.md
├── requirements.txt
├── .env                          # Local credentials (gitignored)
│
├── src/                          # Training pipeline
│   ├── main.py                   # Entry point
│   ├── api/                      # ChirpStack API client
│   ├── processing/               # Feature & Terrain engineering
│   └── ml/                       # Model training & serialization
│
├── coverage_predictor/           # Standalone inference engine
│   ├── predictor.py              # predict(lat, lon) -> RSSI
│   ├── feature_builder.py        # Single-point feature construction
│   ├── neighbor_features.py      # KDTree spatial search
│   ├── terrain.py                # Raster I/O for DEM/Landuse
│   └── data/                     # Local registry & terrain assets
│
└── data/                         # Global raw & processed datasets
```
