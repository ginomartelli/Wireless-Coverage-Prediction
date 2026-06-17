"""
Wireless Coverage Prediction — Web Dashboard
=============================================
Interactive cartographic dashboard built with Streamlit, Folium & Plotly.

Features:
  - Dual map system: Raw data (top) + Prediction coverage (bottom)
  - Dynamic gateway filtering with pre-computed predictions
  - RSSI signal legend with standard color scale

Run locally:
    streamlit run app.py

Run with Docker:
    docker-compose up web-dashboard
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path
from typing import Any

import branca.colormap as cm
import folium
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from folium.plugins import HeatMap, MarkerCluster
from streamlit_folium import st_folium

import concurrent.futures
import threading

# -- Path setup --------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent
COV_PREDICTOR = PROJECT_ROOT / "coverage_predictor"

for p in [str(PROJECT_ROOT), str(COV_PREDICTOR)]:
    if p not in sys.path:
        sys.path.insert(0, p)

# -- Graceful startup: catch config / file errors ---------------------------
try:
    from config_loader import config

    INF_CFG = config["paths"]["inference"]
    RADIO = config["radio"]

    BASE_DIR = str(COV_PREDICTOR)

    # Verify that essential data files exist
    _gateways_path = os.path.join(BASE_DIR, INF_CFG["gateways_csv"])
    _ref_path = os.path.join(BASE_DIR, INF_CFG["reference_csv"])
    _terrain_dir = os.path.join(BASE_DIR, INF_CFG["terrain_dir"])

    if not os.path.isfile(_gateways_path):
        st.error(f"Gateways file not found: {_gateways_path}")
        st.stop()
    if not os.path.isfile(_ref_path):
        st.error(f"Reference points file not found: {_ref_path}")
        st.stop()
    if not os.path.isdir(_terrain_dir):
        st.warning(f"Terrain directory not found: {_terrain_dir}. Terrain overlays will be unavailable.")

except Exception as _startup_err:
    st.error(f"Failed to load configuration: {_startup_err}")
    st.info("Make sure config.yaml exists at the project root.")
    st.stop()

# -- Page config ------------------------------------------------------------
st.set_page_config(
    page_title="Wireless Coverage Dashboard",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for cleaner layout
st.markdown(
    """
<style>
    .main > div { padding: 0 1rem; }
    .stApp header {
        background-color: #ffffff !important;
        color: #1a1a2e !important;
    }
    .stApp header button,
    .stApp header button p,
    .stApp header span,
    .stApp header div[data-testid="stToolbar"] button,
    .stApp header div[data-testid="stDecoration"] {
        color: #1a1a2e !important;
    }
    .stApp header svg {
        fill: #1a1a2e !important;
    }
    .stApp header button:hover {
        background-color: #f0f2f6 !important;
    }
    div[data-testid="stToolbar"] {
        border-bottom: 1px solid #e0e0e0 !important;
    }
    .gateway-metric {
        background: #f8f9fa;
        border-radius: 8px;
        padding: 12px 16px;
        border: 1px solid #e9ecef;
        margin-bottom: 8px;
    }
    .gateway-metric .label {
        font-size: 0.75rem;
        color: #6c757d;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .gateway-metric .value {
        font-size: 1.1rem;
        font-weight: 600;
        color: #1a1a2e;
    }
    .map-section-title {
        font-size: 1.1rem;
        font-weight: 600;
        margin-bottom: 4px;
        padding: 0;
    }
    .map-section-subtitle {
        font-size: 0.85rem;
        color: #6c757d;
        margin-bottom: 8px;
    }
    div[data-testid="stHorizontalBlock"] {
        gap: 1rem;
    }
</style>
""",
    unsafe_allow_html=True,
)

# ============================================================================
# RSSI COLOR SCALE -- constants used across both maps
# ============================================================================

# Nouvelle echelle inversee : rouge = signal fort, bleu fonce = signal faible
RSSI_LEGEND_COLORS = {
    "fort": "#cc0000",          # > -100 dBm  (Signal Fort)
    "moyen_fort": "#ff8000",    # -100 a -105 dBm
    "moyen": "#ffcc00",         # -105 a -110 dBm
    "faible": "#00b300",        # -110 a -115 dBm
    "tres_faible": "#00cccc",   # -115 a -120 dBm
    "critique": "#0000cc",      # < -120 dBm  (Signal Faible)
}


def rssi_to_color(rssi: float) -> str:
    """Map an RSSI value (dBm) to a colour using the inverted scale.

    Fort signal = red, weak signal = dark blue.
    """
    if pd.isna(rssi):
        return "#888888"
    if rssi > -100:
        return RSSI_LEGEND_COLORS["fort"]
    elif rssi >= -105:
        return RSSI_LEGEND_COLORS["moyen_fort"]
    elif rssi >= -110:
        return RSSI_LEGEND_COLORS["moyen"]
    elif rssi >= -115:
        return RSSI_LEGEND_COLORS["faible"]
    elif rssi >= -120:
        return RSSI_LEGEND_COLORS["tres_faible"]
    else:
        return RSSI_LEGEND_COLORS["critique"]


def _rssi_legend_html(title: str = "RSSI (dBm)") -> str:
    """Return an HTML string for the RSSI colour legend overlay."""
    items = [
        ("> -100", "Signal Fort", RSSI_LEGEND_COLORS["fort"]),
        ("-100 a -105", "Moyen-Fort", RSSI_LEGEND_COLORS["moyen_fort"]),
        ("-105 a -110", "Moyen", RSSI_LEGEND_COLORS["moyen"]),
        ("-110 a -115", "Faible", RSSI_LEGEND_COLORS["faible"]),
        ("-115 a -120", "Tres Faible", RSSI_LEGEND_COLORS["tres_faible"]),
        ("< -120", "Critique", RSSI_LEGEND_COLORS["critique"]),
    ]
    rows = "".join(
        f"""<tr>
            <td style="width:18px;height:14px;background:{color};border-radius:2px;"></td>
            <td style="padding-left:6px;font-size:11px;line-height:1.5;">{label}</td>
            <td style="padding-left:8px;font-size:10px;color:#777;line-height:1.5;">{desc}</td>
        </tr>"""
        for label, desc, color in items
    )
    return f"""
    <div style="
        position:absolute; bottom:24px; right:16px; z-index:9999;
        background:rgba(255,255,255,0.95); padding:10px 14px;
        border-radius:6px; box-shadow:0 1px 6px rgba(0,0,0,0.2);
        font-family:system-ui,-apple-system,sans-serif;
        min-width:130px;
    ">
        <div style="font-weight:700;font-size:12px;margin-bottom:4px;">{title}</div>
        <table>{rows}</table>
    </div>"""


def _add_rssi_legend_to_map(m: folium.Map, title: str = "RSSI (dBm)") -> None:
    """Inject the RSSI legend overlay into a Folium map."""
    folium.Element(_rssi_legend_html(title)).add_to(m)


# ============================================================================
# DATA LOADING (frozen at startup -- "mode fige")
# ============================================================================


@st.cache_resource(show_spinner="Loading gateways & reference points...")
def load_gateways() -> pd.DataFrame:
    path = os.path.join(BASE_DIR, INF_CFG["gateways_csv"])
    return pd.read_csv(path)


@st.cache_resource(show_spinner="Loading reference measurements...")
def load_reference_points() -> pd.DataFrame:
    path = os.path.join(BASE_DIR, INF_CFG["reference_csv"])
    return pd.read_csv(path)


@st.cache_resource(show_spinner="Initialising prediction engine...")
def load_predictor():
    """Import and return the predictor module (lazy model loading)."""
    import coverage_predictor.predictor as pred_mod
    return pred_mod


@st.cache_resource(show_spinner="Loading terrain data...")
def load_terrain_geojson():
    """Load land-use polygons as GeoJSON for Folium overlay."""
    import json
    import geopandas as gpd

    terrain_dir = os.path.join(BASE_DIR, INF_CFG["terrain_dir"])
    landuse_path = os.path.join(terrain_dir, INF_CFG["landuse_geojson"])
    landuse2_path = os.path.join(terrain_dir, INF_CFG["landuse2_geojson"])

    geojson_layers: list[dict] = []

    for path, label in [(landuse_path, "landuse"), (landuse2_path, "landuse2")]:
        if os.path.isfile(path):
            gdf = gpd.read_file(path)
            for col in gdf.columns:
                if gdf[col].dtype == "datetime64[ns]" or "datetime" in str(gdf[col].dtype):
                    gdf[col] = gdf[col].astype(str)
            geojson_layers.append({"data": json.loads(gdf.to_json()), "label": label})

    return geojson_layers


# -- Region definitions based on gateway clusters ---------------------------


def _define_regions(gw: pd.DataFrame) -> list[dict[str, Any]]:
    """Cluster gateways by geographic proximity to define prediction regions."""
    regions = []
    gw_coords = gw[["gw_lat", "gw_lon"]].drop_duplicates().values

    used = set()
    for i, (lat, lon) in enumerate(gw_coords):
        if i in used:
            continue
        cluster = [(lat, lon)]
        used.add(i)
        for j, (lat2, lon2) in enumerate(gw_coords):
            if j in used:
                continue
            dist_deg = np.sqrt((lat - lat2) ** 2 + (lon - lon2) ** 2)
            if dist_deg < 1.0:
                cluster.append((lat2, lon2))
                used.add(j)

        lats = [c[0] for c in cluster]
        lons = [c[1] for c in cluster]
        center_lat = np.mean(lats)
        center_lon = np.mean(lons)
        pad = 0.05

        regions.append({
            "name": f"Region {len(regions) + 1}",
            "center": (center_lat, center_lon),
            "bounds": {
                "lat_min": min(lats) - pad,
                "lat_max": max(lats) + pad,
                "lon_min": min(lons) - pad,
                "lon_max": max(lons) + pad,
            },
            "gateway_count": len(cluster),
        })

    for r in regions:
        lat = r["center"][0]
        if lat > 18:
            r["name"] = "Hai Phong"
        else:
            r["name"] = "Da Nang"

    return regions


# ============================================================================
# GATEWAY HELPERS
# ============================================================================


def get_unique_gateway_ids(gateways: pd.DataFrame) -> list[str]:
    """Return sorted list of unique gateway IDs."""
    return sorted(gateways["gateway"].unique().tolist())


def get_gateway_entries(gateways: pd.DataFrame, gw_id: str) -> pd.DataFrame:
    """Return all rows for a given gateway ID."""
    return gateways[gateways["gateway"] == gw_id]


def get_gateway_center(gateways: pd.DataFrame, gw_id: str) -> tuple[float, float]:
    """Return the average (lat, lon) for a gateway."""
    entries = get_gateway_entries(gateways, gw_id)
    return (entries["gw_lat"].mean(), entries["gw_lon"].mean())


def get_gateway_bounds(gateways: pd.DataFrame, gw_id: str, padding_deg: float = 0.02) -> dict:
    """Return bounds surrounding a gateway with padding, limited to its range."""
    entries = get_gateway_entries(gateways, gw_id)
    lat = entries["gw_lat"].mean()
    lon = entries["gw_lon"].mean()
    max_range_m = entries["range"].max()

    range_deg = max_range_m / 111000.0
    pad = max(range_deg + 0.005, padding_deg)

    return {
        "lat_min": lat - pad,
        "lat_max": lat + pad,
        "lon_min": lon - pad,
        "lon_max": lon + pad,
    }


def get_gateway_metrics(gateways: pd.DataFrame, gw_id: str) -> dict:
    """Return technical characteristics for a gateway."""
    entries = get_gateway_entries(gateways, gw_id)
    first = entries.iloc[0]
    return {
        "gateway_id": gw_id,
        "lat": entries["gw_lat"].mean(),
        "lon": entries["gw_lon"].mean(),
        "elevation": first["gw_elevation"],
        "range_m": entries["range"].max(),
        "num_entries": len(entries),
        "num_ref_points": 0,
    }


# ============================================================================
# PREDICTION GRID GENERATION (frozen at startup)
# ============================================================================


_PREDICT_LOCK = threading.Lock()
_PREDICT_TIMEOUT_S = 5


def _predict_one(predictor_mod, lat: float, lon: float, gateway: str | None = None) -> dict:
    """Run a single prediction with a timeout."""
    with _PREDICT_LOCK:
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            fut = pool.submit(predictor_mod.predict, float(lat), float(lon), gateway)
            try:
                result = fut.result(timeout=_PREDICT_TIMEOUT_S)
                return {
                    "lat": float(lat),
                    "lon": float(lon),
                    "rssi": float(result["rssi"]) if result["rssi"] is not None else np.nan,
                    "ood": bool(result["ood"]),
                    "skipped": False,
                }
            except concurrent.futures.TimeoutError:
                return {"lat": float(lat), "lon": float(lon), "rssi": np.nan, "ood": True, "skipped": True}
            except Exception:
                return {"lat": float(lat), "lon": float(lon), "rssi": np.nan, "ood": True, "skipped": True}


def generate_prediction_grid(
    region_bounds: dict, grid_resolution: int = 10, gateway: str | None = None
) -> pd.DataFrame:
    """Generate and predict RSSI for a grid of points in the given region."""
    lat_min = region_bounds["lat_min"]
    lat_max = region_bounds["lat_max"]
    lon_min = region_bounds["lon_min"]
    lon_max = region_bounds["lon_max"]

    lats = np.linspace(lat_min, lat_max, grid_resolution)
    lons = np.linspace(lon_min, lon_max, grid_resolution)

    grid_lats, grid_lons = np.meshgrid(lats, lons)
    points = np.column_stack([grid_lats.ravel(), grid_lons.ravel()])

    predictor_mod = load_predictor()

    results: list[dict] = []
    total = len(points)
    progress_bar = st.progress(0.0, text=f"Predicting RSSI for {total} grid points...")
    skipped_count = 0

    for idx, (lat, lon) in enumerate(points):
        row = _predict_one(predictor_mod, lat, lon, gateway=gateway)
        results.append(row)
        if row["skipped"]:
            skipped_count += 1
        if (idx + 1) % max(1, total // 20) == 0 or idx == total - 1:
            label = f"Predicting RSSI... {idx + 1}/{total}"
            if skipped_count:
                label += f" ({skipped_count} skipped)"
            progress_bar.progress((idx + 1) / total, text=label)

    progress_bar.progress(1.0, text="Prediction complete!")
    time.sleep(0.3)
    progress_bar.empty()

    if skipped_count:
        gw_label = f"gateway {gateway}" if gateway else "all gateways"
        st.info(
            f"Warning: {skipped_count} / {total} grid points for {gw_label} were skipped "
            f"(predictions took > {_PREDICT_TIMEOUT_S}s each). Try a coarser grid."
        )

    return pd.DataFrame(results)


# ============================================================================
# MAP BUILDERS
# ============================================================================


def build_raw_data_map(
    region: dict,
    gateways: pd.DataFrame,
    ref_points: pd.DataFrame,
    selected_gateway: str | None,
    terrain_geojsons: list[dict],
    show_gateways: bool = True,
    show_terrain: bool = False,
    show_heatmap: bool = True,
) -> folium.Map:
    """Build the top map showing raw measurement data."""
    # Determine centre and bounds
    if selected_gateway and selected_gateway != "__all__":
        center_lat, center_lon = get_gateway_center(gateways, selected_gateway)
        zoom = 16
        ref_display = ref_points[ref_points["gateway"] == selected_gateway].copy()
        gw_display = get_gateway_entries(gateways, selected_gateway)
    else:
        center_lat, center_lon = region["center"]
        zoom = 14
        ref_display = ref_points.copy()
        gw_display = gateways

    m = folium.Map(location=[center_lat, center_lon], zoom_start=zoom, control_scale=True)

    # 1. Terrain overlay
    if show_terrain:
        _add_terrain_layers(m, terrain_geojsons)

    # 2. Reference points coloured by actual RSSI
    if not ref_display.empty:
        for _, pt in ref_display.iterrows():
            color = rssi_to_color(pt["rssi"])
            radius = 6
            if pt["rssi"] > -100:
                radius = 8
            elif pt["rssi"] >= -110:
                radius = 7

            folium.CircleMarker(
                location=[pt["lat"], pt["lon"]],
                radius=radius,
                color=color,
                fill=True,
                fill_color=color,
                fill_opacity=0.7,
                weight=1,
                popup=(
                    f"<b>RSSI:</b> {pt['rssi']:.0f} dBm<br>"
                    f"<b>Gateway:</b> {pt['gateway']}<br>"
                    f"<b>Distance:</b> {pt['distance']:.0f} m"
                ),
                tooltip=f"{pt['rssi']:.0f} dBm",
            ).add_to(m)

        # RSSI Heatmap overlay
        if show_heatmap:
            heat_data = [
                [row["lat"], row["lon"], max(row["rssi"], -130)]
                for _, row in ref_display.iterrows()
                if not np.isnan(row["rssi"])
            ]
            if heat_data:
                HeatMap(
                    heat_data,
                    min_opacity=0.3,
                    max_zoom=14,
                    radius=20,
                    blur=15,
                    gradient={0.0: "#0000cc", 0.2: "#00cccc", 0.4: "#00b300", 0.6: "#ffcc00", 0.8: "#ff8000", 1.0: "#cc0000"},
                    name="RSSI Heatmap",
                ).add_to(m)

    # 3. Gateway markers
    if show_gateways:
        gw_unique = gw_display.drop_duplicates(subset=["gateway", "gw_lat", "gw_lon"])
        gw_cluster = MarkerCluster(name="Gateways").add_to(m)

        for _, gw in gw_unique.iterrows():
            popup_html = (
                f"<b>Gateway:</b> {gw['gateway']}<br>"
                f"<b>Lat:</b> {gw['gw_lat']:.5f}<br>"
                f"<b>Lon:</b> {gw['gw_lon']:.5f}<br>"
                f"<b>Elevation:</b> {gw['gw_elevation']:.1f} m<br>"
                f"<b>Range:</b> {gw['range']:.0f} m"
            )
            folium.Marker(
                location=[gw["gw_lat"], gw["gw_lon"]],
                popup=folium.Popup(popup_html, max_width=300),
                tooltip=gw["gateway"],
                icon=folium.Icon(color="red", icon="wifi", prefix="fa"),
            ).add_to(gw_cluster)

    # 4. RSSI Legend
    _add_rssi_legend_to_map(m, title="RSSI mesure (dBm)")

    # Layer control
    folium.LayerControl(collapsed=False).add_to(m)

    return m


def build_prediction_map(
    region: dict,
    gateways: pd.DataFrame,
    pred_grid: pd.DataFrame | None,
    selected_gateway: str | None,
    terrain_geojsons: list[dict],
    show_gateways: bool = True,
    show_terrain: bool = False,
) -> folium.Map:
    """Build the bottom map showing the prediction coverage heatmap."""
    if selected_gateway and selected_gateway != "__all__":
        center_lat, center_lon = get_gateway_center(gateways, selected_gateway)
        zoom = 15
    else:
        center_lat, center_lon = region["center"]
        zoom = 14

    m = folium.Map(location=[center_lat, center_lon], zoom_start=zoom, control_scale=True)

    # 1. Terrain overlay
    if show_terrain:
        _add_terrain_layers(m, terrain_geojsons)

    # 2. Prediction grid layer
    if pred_grid is not None and not pred_grid.empty:
        valid = pred_grid.dropna(subset=["rssi"])
        if not valid.empty:
            rssi_min, rssi_max = valid["rssi"].min(), valid["rssi"].max()
            colormap = cm.LinearColormap(
                colors=["#0000cc", "#00cccc", "#00b300", "#ffcc00", "#ff8000", "#cc0000"],
                vmin=min(rssi_min, -110),
                vmax=max(rssi_max, -50),
                caption="RSSI predit (dBm)",
            )

            for _, pt in valid.iterrows():
                folium.CircleMarker(
                    location=[pt["lat"], pt["lon"]],
                    radius=6,
                    color=rssi_to_color(pt["rssi"]),
                    fill=True,
                    fill_color=rssi_to_color(pt["rssi"]),
                    fill_opacity=0.75,
                    weight=1.5,
                    popup=f"<b>RSSI predit:</b> {pt['rssi']:.1f} dBm<br><b>OOD:</b> {pt['ood']}",
                    tooltip=f"{pt['rssi']:.1f} dBm",
                ).add_to(m)

            m.add_child(colormap)

    # 3. Gateway markers (lightweight, no cluster)
    if show_gateways:
        if selected_gateway and selected_gateway != "__all__":
            gw_display = get_gateway_entries(gateways, selected_gateway)
        else:
            gw_display = gateways

        gw_unique = gw_display.drop_duplicates(subset=["gateway", "gw_lat", "gw_lon"])
        for _, gw in gw_unique.iterrows():
            folium.Marker(
                location=[gw["gw_lat"], gw["gw_lon"]],
                icon=folium.Icon(color="red", icon="wifi", prefix="fa", icon_color="white"),
                tooltip=gw["gateway"],
            ).add_to(m)

    # 4. RSSI Legend
    _add_rssi_legend_to_map(m, title="RSSI predit (dBm)")

    # Layer control
    folium.LayerControl(collapsed=False).add_to(m)

    return m


# -- Shared terrain helper --------------------------------------------------


def _add_terrain_layers(m: folium.Map, terrain_geojsons: list[dict]) -> None:
    """Add land-use GeoJSON overlays to a map."""
    terrain_colors = {
        "residential": "#ff7f7f",
        "forest": "#7fbf7f",
        "water": "#7f7fff",
        "industrial": "#bf7fbf",
        "farmland": "#ffff7f",
        "grass": "#bfff7f",
    }
    default_color = "#d0d0d0"

    for layer in terrain_geojsons:
        folium.GeoJson(
            data=layer["data"],
            name=f"Terrain ({layer['label']})",
            style_function=lambda feat, _colors=terrain_colors, _def=default_color: {
                "fillColor": _colors.get(
                    feat["properties"].get("landuse")
                    or feat["properties"].get("natural", ""),
                    _def,
                ),
                "color": "#666666",
                "weight": 0.5,
                "fillOpacity": 0.35,
            },
            tooltip=folium.GeoJsonTooltip(
                fields=["landuse", "natural"],
                aliases=["Land use", "Natural"],
                labels=True,
            ),
        ).add_to(m)


# ============================================================================
# PERFORMANCE CHARTS
# ============================================================================


def build_rssi_distribution(
    ref_points: pd.DataFrame, pred_grid: pd.DataFrame | None, selected_gateway: str | None = None
):
    """RSSI distribution histogram (measured vs predicted)."""
    fig = go.Figure()

    if selected_gateway and selected_gateway != "__all__":
        ref_display = ref_points[ref_points["gateway"] == selected_gateway]
    else:
        ref_display = ref_points

    measured = ref_display["rssi"].dropna()
    fig.add_trace(
        go.Histogram(
            x=measured,
            name="Measured",
            opacity=0.7,
            nbinsx=40,
            marker_color="#1f77b4",
        )
    )

    if pred_grid is not None:
        predicted = pred_grid["rssi"].dropna()
        fig.add_trace(
            go.Histogram(
                x=predicted,
                name="Predicted",
                opacity=0.7,
                nbinsx=40,
                marker_color="#ff7f0e",
            )
        )

    fig.update_layout(
        title="RSSI Distribution (Measured vs Predicted)",
        xaxis_title="RSSI (dBm)",
        yaxis_title="Count",
        barmode="overlay",
        height=350,
        margin=dict(l=40, r=20, t=40, b=40),
        legend=dict(yanchor="top", y=0.98, xanchor="right", x=0.98),
    )
    return fig


def build_signal_loss_vs_distance(ref_points: pd.DataFrame, selected_gateway: str | None = None):
    """Scatter plot: RSSI vs distance to nearest gateway."""
    if selected_gateway and selected_gateway != "__all__":
        df = ref_points[ref_points["gateway"] == selected_gateway].dropna(subset=["rssi", "distance"]).copy()
    else:
        df = ref_points.dropna(subset=["rssi", "distance"]).copy()

    if df.empty:
        fig = go.Figure()
        fig.update_layout(title="Signal Loss vs Distance (no data)", height=350)
        return fig

    df["distance_km"] = df["distance"] / 1000

    fig = px.scatter(
        df,
        x="distance_km",
        y="rssi",
        color="rssi",
        color_continuous_scale="RdYlGn_r",
        opacity=0.5,
        labels={"distance_km": "Distance to Gateway (km)", "rssi": "RSSI (dBm)"},
        title="Signal Loss vs Distance to Gateway",
    )

    valid = df[df["distance_km"] > 0]
    if len(valid) > 5:
        coeffs = np.polyfit(valid["distance_km"], valid["rssi"], 2)
        x_trend = np.linspace(valid["distance_km"].min(), valid["distance_km"].max(), 100)
        y_trend = np.polyval(coeffs, x_trend)
        fig.add_trace(
            go.Scatter(
                x=x_trend,
                y=y_trend,
                mode="lines",
                name="Trend (poly2)",
                line=dict(color="black", width=2, dash="dash"),
            )
        )

    fig.update_layout(height=350, margin=dict(l=40, r=20, t=40, b=40))
    return fig


def build_rssi_by_gateway(ref_points: pd.DataFrame, selected_gateway: str | None = None):
    """Box plot of RSSI per gateway."""
    df = ref_points.dropna(subset=["rssi", "gateway"]).copy()

    if selected_gateway and selected_gateway != "__all__":
        df = df[df["gateway"] == selected_gateway]
        fig = px.box(
            df,
            x="gateway",
            y="rssi",
            color="gateway",
            labels={"gateway": "Gateway", "rssi": "RSSI (dBm)"},
            title=f"RSSI Distribution - {selected_gateway[:12]}...",
            height=350,
        )
    else:
        top_gws = df["gateway"].value_counts().head(10).index
        df = df[df["gateway"].isin(top_gws)]
        fig = px.box(
            df,
            x="gateway",
            y="rssi",
            color="gateway",
            labels={"gateway": "Gateway", "rssi": "RSSI (dBm)"},
            title="RSSI Distribution per Gateway",
            height=350,
        )

    fig.update_layout(
        showlegend=False,
        margin=dict(l=40, r=20, t=40, b=80),
        xaxis_tickangle=-45,
    )
    return fig


# ============================================================================
# STREAMLIT UI
# ============================================================================


def render_gateway_metrics_section(
    gateways: pd.DataFrame, ref_points: pd.DataFrame, selected_gateway: str | None
):
    """Display technical characteristics of the selected gateway."""
    if not selected_gateway or selected_gateway == "__all__":
        st.info("Select a specific gateway to view its technical characteristics.")
        return

    metrics = get_gateway_metrics(gateways, selected_gateway)
    n_ref = len(ref_points[ref_points["gateway"] == selected_gateway])
    metrics["num_ref_points"] = n_ref

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.markdown(
            f"<div class='gateway-metric'><div class='label'>Gateway ID</div>"
            f"<div class='value' style='font-size:0.9rem;'>{metrics['gateway_id'][:16]}...</div></div>",
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            f"<div class='gateway-metric'><div class='label'>Coordinates</div>"
            f"<div class='value'>{metrics['lat']:.4f}, {metrics['lon']:.4f}</div></div>",
            unsafe_allow_html=True,
        )
    with col3:
        st.markdown(
            f"<div class='gateway-metric'><div class='label'>Antenna Height</div>"
            f"<div class='value'>{metrics['elevation']:.1f} m</div></div>",
            unsafe_allow_html=True,
        )
    with col4:
        st.markdown(
            f"<div class='gateway-metric'><div class='label'>Max Range</div>"
            f"<div class='value'>{metrics['range_m']:.0f} m</div></div>",
            unsafe_allow_html=True,
        )
    with col5:
        st.markdown(
            f"<div class='gateway-metric'><div class='label'>Ref Points</div>"
            f"<div class='value'>{metrics['num_ref_points']}</div></div>",
            unsafe_allow_html=True,
        )


def main():
    st.title("Wireless Coverage Prediction Dashboard")
    st.markdown(
        "Interactive visualization of LoRaWAN signal coverage, terrain analysis, "
        "and model performance - **frozen at startup** for smooth navigation."
    )

    # -- Load data -----------------------------------------------------------
    with st.spinner("Loading gateways..."):
        gateways_df = load_gateways()
    with st.spinner("Loading reference points..."):
        ref_points = load_reference_points()
    with st.spinner("Loading terrain data..."):
        terrain_geojsons = load_terrain_geojson()

    regions = _define_regions(gateways_df)

    # -- Sidebar -------------------------------------------------------------
    st.sidebar.header("Controls")

    region_names = [r["name"] for r in regions]
    default_region_idx = next(i for i, name in enumerate(region_names) if name == "Da Nang")
    selected_region_name = st.sidebar.selectbox("Region", region_names, index=default_region_idx)
    selected_region = next(r for r in regions if r["name"] == selected_region_name)

    st.sidebar.markdown("---")
    st.sidebar.markdown("**Map Layers**")
    show_gateways = st.sidebar.checkbox("Gateways", value=True)
    show_heatmap = st.sidebar.checkbox("RSSI Heatmap", value=True)
    show_predictions = st.sidebar.checkbox("Prediction Grid", value=True)
    show_terrain = st.sidebar.checkbox("Terrain (Landuse)", value=False)

    st.sidebar.markdown("---")
    st.sidebar.markdown("**Region Stats**")
    gw_in_region = gateways_df[
        (gateways_df["gw_lat"] >= selected_region["bounds"]["lat_min"])
        & (gateways_df["gw_lat"] <= selected_region["bounds"]["lat_max"])
        & (gateways_df["gw_lon"] >= selected_region["bounds"]["lon_min"])
        & (gateways_df["gw_lon"] <= selected_region["bounds"]["lon_max"])
    ]
    st.sidebar.metric("Gateways", gw_in_region["gateway"].nunique())
    st.sidebar.metric("Reference Points", len(ref_points))

    ref_in_region = ref_points[
        (ref_points["lat"] >= selected_region["bounds"]["lat_min"])
        & (ref_points["lat"] <= selected_region["bounds"]["lat_max"])
        & (ref_points["lon"] >= selected_region["bounds"]["lon_min"])
        & (ref_points["lon"] <= selected_region["bounds"]["lon_max"])
    ]
    st.sidebar.metric("In Region", len(ref_in_region))
    st.sidebar.metric(
        "Avg RSSI",
        f"{ref_in_region['rssi'].mean():.1f} dBm" if not ref_in_region.empty else "N/A",
    )

    # -- Sidebar: Prediction controls ------------------------------------
    st.sidebar.markdown("---")
    st.sidebar.markdown("**Coverage Predictions**")
    grid_resolution = st.sidebar.slider(
        "Grid resolution (points per axis)",
        min_value=5,
        max_value=30,
        value=5,
        step=5,
        help="Higher = finer map but slower to compute.",
    )

    # -- GATEWAY SELECTOR ---------------------------------------------------
    st.markdown("---")
    gw_ids = get_unique_gateway_ids(gateways_df)
    gw_options = ["__all__"] + gw_ids
    gw_labels = ["All Gateways"] + [f"{gid[:16]}..." for gid in gw_ids]

    selected_gateway_label = st.selectbox(
        "**Filter by Gateway**",
        options=gw_labels,
        index=0,
        help="Select a specific gateway to view its data and coverage, or 'All Gateways' to see everything.",
    )
    selected_idx = gw_labels.index(selected_gateway_label)
    selected_gateway = gw_options[selected_idx]

    st.markdown("---")

    # -- Predicted grid keys ------------------------------------------------
    if selected_gateway == "__all__":
        pred_cache_key = f"pred_grid_{selected_region_name}_{grid_resolution}"
        pred_ready = pred_cache_key in st.session_state
    else:
        gw_slug = selected_gateway.replace(":", "_").replace("-", "_")
        pred_cache_key = f"pred_grid_gw_{gw_slug}_{grid_resolution}"
        pred_ready = pred_cache_key in st.session_state

    # -- Prediction setup (prepare bounds, don't execute yet) -------------
    if selected_gateway == "__all__":
        pred_bounds = selected_region["bounds"]
    else:
        pred_bounds = get_gateway_bounds(gateways_df, selected_gateway)

    pred_grid: pd.DataFrame | None = st.session_state.get(pred_cache_key)
    _gen_flag = f"_generating_{pred_cache_key}"

    # Show sidebar status for predictions
    if pred_ready:
        st.sidebar.success(f"Predictions loaded ({grid_resolution}x{grid_resolution})")
        if st.sidebar.button("Regenerate", use_container_width=True):
            del st.session_state[pred_cache_key]
            if _gen_flag in st.session_state:
                del st.session_state[_gen_flag]
            st.rerun()

    # -- Gateway Metrics Section --------------------------------------------
    st.subheader("Gateway Characteristics")
    render_gateway_metrics_section(gateways_df, ref_points, selected_gateway)

    # -- MAP 1: Raw Data ----------------------------------------------------
    st.markdown(
        "<div class='map-section-title'>Map 1 - Donnees Brutes</div>"
        "<div class='map-section-subtitle'>Points de reference reels et mesures RSSI terrain</div>",
        unsafe_allow_html=True,
    )

    if selected_gateway and selected_gateway != "__all__":
        ref_raw = ref_points[ref_points["gateway"] == selected_gateway]
    else:
        ref_raw = ref_points[
            (ref_points["lat"] >= selected_region["bounds"]["lat_min"])
            & (ref_points["lat"] <= selected_region["bounds"]["lat_max"])
            & (ref_points["lon"] >= selected_region["bounds"]["lon_min"])
            & (ref_points["lon"] <= selected_region["bounds"]["lon_max"])
        ]

    raw_map = build_raw_data_map(
        region=selected_region,
        gateways=gateways_df,
        ref_points=ref_raw,
        selected_gateway=selected_gateway,
        terrain_geojsons=terrain_geojsons,
        show_gateways=show_gateways,
        show_terrain=show_terrain,
        show_heatmap=show_heatmap,
    )
    st_folium(raw_map, use_container_width=True, height=500)

    # -- MAP 2: Prediction Coverage -----------------------------------------
    st.markdown(
        "<div class='map-section-title'>Map 2 - Couverture Predite</div>"
        "<div class='map-section-subtitle'>Heatmap de couverture generee par le modele predictif</div>",
        unsafe_allow_html=True,
    )

    pred_map = build_prediction_map(
        region=selected_region,
        gateways=gateways_df,
        pred_grid=pred_grid if (show_predictions and pred_ready) else None,
        selected_gateway=selected_gateway,
        terrain_geojsons=terrain_geojsons,
        show_gateways=show_gateways,
        show_terrain=show_terrain,
    )
    st_folium(pred_map, use_container_width=True, height=500)

    # -- Performance Charts -------------------------------------------------
    st.markdown("---")
    st.subheader("Performance Visualizations")

    col1, col2 = st.columns(2)

    with col1:
        fig_rssi_dist = build_rssi_distribution(ref_points, pred_grid, selected_gateway)
        st.plotly_chart(fig_rssi_dist, use_container_width=True)

    with col2:
        fig_loss = build_signal_loss_vs_distance(ref_points, selected_gateway)
        st.plotly_chart(fig_loss, use_container_width=True)

    fig_gw = build_rssi_by_gateway(ref_points, selected_gateway)
    st.plotly_chart(fig_gw, use_container_width=True)

    # -- Auto-generate predictions AFTER maps are rendered ------------------
    # This ensures maps show immediately; predictions update on next rerun
    if not pred_ready and not st.session_state.get(_gen_flag, False):
        st.session_state[_gen_flag] = True
        gw_param = selected_gateway if selected_gateway != "__all__" else None
        n_points = grid_resolution * grid_resolution
        st.sidebar.info(
            f"Generating {grid_resolution}x{grid_resolution} coverage prediction "
            f"({n_points} points)... This may take a moment."
        )
        try:
            st.session_state[pred_cache_key] = generate_prediction_grid(
                pred_bounds,
                grid_resolution=grid_resolution,
                gateway=gw_param,
            )
        except Exception as e:
            if _gen_flag in st.session_state:
                del st.session_state[_gen_flag]
            st.error(f"Coverage prediction failed: {e}")
            st.stop()
        st.rerun()

    # -- Data tables (expandable) -------------------------------------------
    with st.expander("Raw Data Preview"):
        tab1, tab2 = st.tabs(["Gateways", "Reference Points"])
        with tab1:
            st.dataframe(gateways_df, use_container_width=True, height=300)
        with tab2:
            st.dataframe(ref_points.head(1000), use_container_width=True, height=300)


if __name__ == "__main__":
    main()
