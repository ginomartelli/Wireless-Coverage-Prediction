# LoRaWAN RSSI Prediction Framework

Machine learning framework for LoRaWAN RSSI prediction using historical measurements, terrain information, and spatial neighborhood features.

The repository contains both the complete training pipeline used to develop the model and a standalone prediction engine that can be deployed independently.

---

# Repository Structure

```text
.
├── coverage_predictor/
│   ├── predictor.py
│   ├── feature_builder.py
│   ├── ...
│   └── README.md
│
├── data/
│   ├── raw/
│   ├── processed/
│   └── terrain/
│
├── src/
│   ├── api/
│   ├── processing/
│   ├── ml/
│   └── ...
│
├── requirements.txt
├── .gitignore
└── README.md
```

---

# Components

## Data Acquisition

The `src/api/` module contains utilities for retrieving LoRaWAN measurements from external APIs.

Collected records typically include:

* device coordinates,
* gateway information,
* RSSI measurements,
* radio configuration parameters,
* timestamps.

The downloaded datasets are stored in the `data/` directory for subsequent processing.

---

## Offline Training Pipeline

The `src/` directory contains the complete machine learning workflow used to create the final prediction model.

Main stages include:

### Data Processing

* parsing raw measurements,
* data validation,
* duplicate handling,
* dataset cleaning,
* dataset preparation.

### Terrain Processing

Terrain information is extracted from:

* Digital Elevation Models (DEM),
* OpenStreetMap (OSM) data.

The generated terrain datasets are stored in:

```text
data/terrain/
```

and reused throughout the project.

### Feature Engineering

The framework generates several feature categories:

* radio features,
* geometric features,
* terrain descriptors,
* propagation indicators,
* nearest-neighbor statistics.

### Model Training

Several regression algorithms were evaluated during development, including:

* Random Forest,
* Extra Trees,
* HistGradientBoosting,
* Support Vector Regression,
* Multi-Layer Perceptron.

The final model selected for deployment is an Extra Trees Regressor.

Training scripts, evaluation tools, and optimization procedures are located in:

```text
src/ml/
```

---

## Standalone Prediction Engine

The `coverage_predictor/` directory contains a lightweight deployment-ready inference engine.

Unlike the training pipeline, this module only performs:

* resource loading,
* feature generation,
* RSSI prediction.

The prediction engine is completely independent from the training code and can be integrated into external applications without requiring the full machine learning workflow.

Detailed documentation is available in:

```text
coverage_predictor/README.md
```

---

# Data Directory

The `data/` directory stores all datasets required during development.

Typical contents include:

```text
data/
├── raw/
├── processed/
└── terrain/
```

### raw/

Original downloaded measurements.

### processed/

Cleaned and prepared datasets used for training and evaluation.

### terrain/

Terrain-related resources such as:

* DEM rasters,
* OSM-derived datasets,
* land-use information.

---

# Installation

Clone the repository:

```bash
git clone <repository-url>
cd <repository-name>
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

# Workflow

The typical workflow is:

1. Download measurement data.
2. Process and clean the dataset.
3. Generate terrain and spatial features.
4. Train and evaluate machine learning models.
5. Export the selected model.
6. Deploy the model using the standalone prediction engine.


