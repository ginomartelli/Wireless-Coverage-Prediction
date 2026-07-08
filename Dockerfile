# =============================================================================
# Wireless Coverage Prediction — Multi-stage Dockerfile
# =============================================================================
# Stage 1: Builder — install system dependencies (GDAL, GEOS, PROJ) and
#           compile all Python packages. This stage is never run directly.
# =============================================================================
FROM python:3.12-slim AS builder

# Prevent interactive prompts during apt
ENV DEBIAN_FRONTEND=noninteractive

# Install system libraries required to build geospatial Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    gdal-bin \
    libgdal-dev \
    g++ \
    libgeos-dev \
    libproj-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

# Install Python dependencies (all versions pinned for reproducibility)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


# =============================================================================
# Stage 2: Inference Runner — minimal image for coverage_predictor/
#           Optimised for repeated predict(lat, lon) calls.
# =============================================================================
FROM python:3.12-slim AS inference

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Runtime geospatial shared libraries (only -dev for reliability on slim images)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgdal-dev \
    libgeos-dev \
    libproj-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy the full Python environment from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

WORKDIR /app/coverage_predictor

# Copy inference engine code and static assets (CSV, model .pkl)
COPY coverage_predictor/ .

# Declare the terrain data mount point (large GeoTIFF / GeoJSON files)
# Users MUST mount ./data/terrain/ here or provide their own files
VOLUME ["/app/coverage_predictor/data/terrain"]

# Print usage instructions on container start (do NOT import predictor —
# that requires mounted terrain data which isn't guaranteed at build time)
CMD echo "✔ Inference engine container ready." \
  && echo "" \
  && echo "Mount your terrain data and run predictions:" \
  && echo "  docker exec -it coverage-inference python -c '" \
  && echo "    from predictor import predict;" \
  && echo "    print(predict(16.0735, 108.1512))" \
  && echo "  '"


# =============================================================================
# Stage 3: Training — full build environment for running src/main.py
#           Includes the API client, processing pipeline, and training logic.
# =============================================================================
FROM builder AS training

WORKDIR /app

# Copy the full source tree
COPY src/ ./src/
COPY coverage_predictor/ ./coverage_predictor/

# Declare data mount points
#   ./data/processed/   → historical device measurements
#   ./data/terrain/     → DEM TIFFs and land-use GeoJSON files
#   ./data/raw/         → raw API exports
VOLUME ["/app/data"]

WORKDIR /app/src

CMD ["python", "main.py"]


# =============================================================================
# Stage 4: Dashboard — Streamlit web dashboard for coverage visualisation
#           Serves the interactive map dashboard on port 8501.
# =============================================================================
FROM python:3.12-slim AS dashboard

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Runtime geospatial shared libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgdal-dev \
    libgeos-dev \
    libproj-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy the full Python environment from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

WORKDIR /app

# Copy the application code
COPY app.py ./
COPY config.yaml ./
COPY config_loader.py ./
COPY coverage_predictor/ ./coverage_predictor/

# Declare mount points
VOLUME ["/app/coverage_predictor/data/terrain"]

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8501/_stcore/health')"

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true"]
