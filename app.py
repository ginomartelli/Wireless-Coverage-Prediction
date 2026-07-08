"""
Wireless Coverage Prediction — Interactive Dashboard
====================================================
Streamlit-based web application with two interactive Folium maps:
  - Map 1 : Historical / terrain coverage data (from coverage.csv)
  - Map 2 : Predictive heatmap (from Extra-Trees ML model)

Usage:
    streamlit run app.py
"""

from __future__ import annotations

import os
import sys
from typing import Any

import numpy as np
import pandas as pd
import streamlit as st
import folium
from folium.plugins import HeatMap
from streamlit_folium import st_folium

# ── Ensure project root is importable ──────────────────────────
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

# Use the project's config_loader to resolve all paths
from config_loader import config as CFG  # noqa: E402

INF_CFG = CFG["paths"]["inference"]
# Convert relative inference paths to absolute (relative to coverage_predictor/)
COV_DIR = os.path.join(PROJECT_ROOT, "coverage_predictor")
GATEWAYS_PATH = os.path.join(COV_DIR, INF_CFG["gateways_csv"])
REFERENCE_PATH = os.path.join(COV_DIR, INF_CFG["reference_csv"])
COVERAGE_PATH = os.path.join(COV_DIR, "data", "coverage.csv")

# ╔══════════════════════════════════════════════════════════════╗
# ║  PAGE CONFIG  (must be first Streamlit command)             ║
# ╚══════════════════════════════════════════════════════════════╝
st.set_page_config(
    page_title="Wireless Coverage Prediction – Dashboard",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ╔══════════════════════════════════════════════════════════════╗
# ║  CONSTANTS                                                  ║
# ╚══════════════════════════════════════════════════════════════╝

# Da Nang study area
DA_NANG_LAT = 16.05
DA_NANG_LON = 108.20
ZOOM_START = 12

# Da Nang bounding box (from plot.py + coverage.csv inspection)
LAT_MIN, LAT_MAX = 15.87, 16.12
LON_MIN, LON_MAX = 108.08, 108.32

# Grid step for predictive heatmap (0.002–0.005 per spec)
GRID_STEP = 0.005

# RSSI colour scale (inverted: red = strong signal)
RSSI_COLORS_HEX = ["#0047AB", "#00FFFF", "#00AA00", "#FFFF00", "#FFA500", "#FF0000"]
RSSI_LABELS = [
    "< -120 dBm  (Faible)",
    "-120 à -115 dBm",
    "-115 à -110 dBm",
    "-110 à -105 dBm",
    "-105 à -100 dBm",
    "> -100 dBm  (Fort)",
]

# Gradient for folium HeatMap (0 → weak, 1 → strong)
HEATMAP_GRADIENT: dict[float, str] = {
    0.00: "#0047AB",
    0.25: "#00FFFF",
    0.45: "#00AA00",
    0.60: "#FFFF00",
    0.80: "#FFA500",
    1.00: "#FF0000",
}

OOD_RSSI_VALUE = -120.0  # out-of-range sentinel in coverage.csv


# ╔══════════════════════════════════════════════════════════════╗
# ║  CACHED DATA LOADERS                                        ║
# ╚══════════════════════════════════════════════════════════════╝

@st.cache_data(show_spinner="Loading gateways…")
def load_gateways() -> pd.DataFrame:
    """Load gateways CSV from config.yaml path."""
    df = pd.read_csv(GATEWAYS_PATH)
    df.columns = df.columns.str.strip()
    return df


@st.cache_data(show_spinner="Loading coverage data…")
def load_coverage() -> pd.DataFrame:
    """Load historical coverage CSV and filter to Da Nang bbox."""
    df = pd.read_csv(COVERAGE_PATH)
    df.columns = df.columns.str.strip()
    mask = (
        (df["lat"] >= LAT_MIN) & (df["lat"] <= LAT_MAX)
        & (df["lon"] >= LON_MIN) & (df["lon"] <= LON_MAX)
    )
    return df[mask].copy()


@st.cache_data(show_spinner="Loading reference points…")
def load_reference_points() -> pd.DataFrame:
    """Load reference points CSV from config.yaml path."""
    df = pd.read_csv(REFERENCE_PATH)
    df.columns = df.columns.str.strip()
    return df


# ╔══════════════════════════════════════════════════════════════╗
# ║  HELPER FUNCTIONS                                           ║
# ╚══════════════════════════════════════════════════════════════╝

def rssi_to_color(rssi: float) -> str:
    """Return the hex colour for a given RSSI value."""
    if pd.isna(rssi) or rssi is None:
        return "#808080"
    if rssi > -100:
        return RSSI_COLORS_HEX[5]  # Red
    if rssi > -105:
        return RSSI_COLORS_HEX[4]  # Orange
    if rssi > -110:
        return RSSI_COLORS_HEX[3]  # Yellow
    if rssi > -115:
        return RSSI_COLORS_HEX[2]  # Green
    if rssi > -120:
        return RSSI_COLORS_HEX[1]  # Cyan
    return RSSI_COLORS_HEX[0]  # Blue


def rssi_to_heatmap_weight(rssi: float) -> float:
    """Normalise RSSI to ``[0, 1]`` for the HeatMap gradient."""
    if pd.isna(rssi) or rssi is None:
        return 0.0
    clipped = np.clip(rssi, -130, -80)
    return float((clipped + 130) / 50.0)


def build_legend_html(title: str = "RSSI (dBm)") -> str:
    """Return an HTML snippet for a fixed legend."""
    items = "".join(
        f"""<div style="display:flex;align-items:center;margin:2px 0;">
            <span style="background:{color};width:14px;height:14px;display:inline-block;
                         margin-right:6px;border-radius:2px;border:1px solid #888;"></span>
            {label}
        </div>"""
        for color, label in zip(RSSI_COLORS_HEX, RSSI_LABELS)
    )
    return f"""
    <div style="
        position:fixed; bottom:24px; left:24px; z-index:9999;
        background:rgba(255,255,255,0.95); padding:10px 14px;
        border-radius:8px; border:1px solid #ccc;
        font-family:'Segoe UI',Arial,sans-serif; font-size:12px;
        box-shadow:0 2px 12px rgba(0,0,0,0.15);
        max-width:210px;
    ">
        <b style="font-size:13px;">{title}</b>
        {items}
    </div>"""


def create_base_map(lat: float, lon: float, zoom: int) -> Any:
    """Return a ``folium.Map`` centred on *lat / lon*."""
    m = folium.Map(
        location=[lat, lon],
        zoom_start=zoom,
        tiles="OpenStreetMap",
        control_scale=True,
        prefer_canvas=True,
    )
    return m


def get_map_centre(
    gateways_df: pd.DataFrame,
    selected_gw: str | None,
    default_zoom: int = ZOOM_START,
) -> tuple[float, float, int]:
    """Determine the map centre and zoom from the selected gateway."""
    if selected_gw:
        gw_row = gateways_df[gateways_df["gateway"] == selected_gw].iloc[0]
        # Clamp centre to Da Nang bounds so we don't drift off the heatmap
        lat = float(np.clip(gw_row["gw_lat"], LAT_MIN, LAT_MAX))
        lon = float(np.clip(gw_row["gw_lon"], LON_MIN, LON_MAX))
        return lat, lon, 14
    return DA_NANG_LAT, DA_NANG_LON, default_zoom


def add_gateway_markers(
    map_obj: Any,
    gateways_df: pd.DataFrame,
    selected_gw: str | None = None,
) -> None:
    """Add tower markers for gateways."""
    if selected_gw:
        subset = gateways_df[gateways_df["gateway"] == selected_gw]
    else:
        subset = gateways_df

    for _, row in subset.iterrows():
        tooltip = (
            f"Gateway: {row['gateway']}<br>"
            f"Lat: {row['gw_lat']:.5f}<br>"
            f"Lon: {row['gw_lon']:.5f}<br>"
            f"Elevation: {row['gw_elevation']} m<br>"
            f"Range: {row['range']:.0f} m"
        )
        folium.Marker(
            location=[row["gw_lat"], row["gw_lon"]],
            icon=folium.Icon(
                icon="broadcast-tower",
                prefix="fa",
                color="red",
                icon_color="white",
            ),
            tooltip=tooltip,
        ).add_to(map_obj)


# ╔══════════════════════════════════════════════════════════════╗
# ║  MAP BUILDERS                                               ║
# ╚══════════════════════════════════════════════════════════════╝

def build_historical_map(
    gateways_df: pd.DataFrame,
    coverage_df: pd.DataFrame,
    ref_df: pd.DataFrame,
    selected_gw: str | None,
) -> Any:
    """Build Map 1 — historical/observed coverage heatmap."""
    centre_lat, centre_lon, zoom = get_map_centre(
        gateways_df, selected_gw, ZOOM_START
    )
    m = create_base_map(centre_lat, centre_lon, zoom)

    # Filter coverage data
    cov = coverage_df.copy()
    if selected_gw:
        cov = cov[cov["gateway"] == selected_gw]

    # Draw HeatMap from coverage data
    if len(cov) > 0:
        cov_display = cov.copy()
        # Shift OOD sentinel to blue range
        cov_display.loc[cov_display["rssi"] == OOD_RSSI_VALUE, "rssi"] = -130.0

        heat_data = [
            [row["lat"], row["lon"], rssi_to_heatmap_weight(row["rssi"])]
            for _, row in cov_display.iterrows()
        ]
        HeatMap(
            heat_data,
            gradient=HEATMAP_GRADIENT,
            min_opacity=0.2,
            max_opacity=0.8,
            radius=15,
            blur=12,
        ).add_to(m)

    # Draw reference points as small circles
    if selected_gw:
        gw_ref = ref_df[ref_df["gateway"] == selected_gw]
    else:
        gw_ref = ref_df

    # Sample reference points to avoid clutter (max 2000)
    if len(gw_ref) > 2000:
        gw_ref = gw_ref.sample(n=2000, random_state=42)

    for _, row in gw_ref.iterrows():
        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=2,
            color=rssi_to_color(row["rssi"]),
            fill=True,
            fill_color=rssi_to_color(row["rssi"]),
            fill_opacity=0.6,
            tooltip=f"RSSI: {row['rssi']:.0f} dBm",
        ).add_to(m)

    add_gateway_markers(m, gateways_df, selected_gw)
    m.get_root().html.add_child(
        folium.Element(build_legend_html("RSSI Historique (dBm)"))
    )
    return m


def build_predictive_map(
    gateways_df: pd.DataFrame,
    coverage_df: pd.DataFrame,
    selected_gw: str | None,
) -> Any:
    """Build Map 2 — ML-predicted coverage heatmap.

    Uses the same ``coverage.csv`` data as Map 1 (which already contains
    the model's predictions for the full Da Nang grid).
    """
    centre_lat, centre_lon, zoom = get_map_centre(
        gateways_df, selected_gw, ZOOM_START
    )
    m = create_base_map(centre_lat, centre_lon, zoom)
    add_gateway_markers(m, gateways_df, selected_gw)

    # Filter coverage data (same source as Map 1)
    cov = coverage_df.copy()
    if selected_gw:
        cov = cov[cov["gateway"] == selected_gw]

    if len(cov) > 0:
        cov_display = cov.copy()
        # Shift -120.0 sentinel to blue range
        cov_display.loc[cov_display["rssi"] == OOD_RSSI_VALUE, "rssi"] = -130.0

        heat_data = [
            [row["lat"], row["lon"], rssi_to_heatmap_weight(row["rssi"])]
            for _, row in cov_display.iterrows()
        ]
        HeatMap(
            heat_data,
            gradient=HEATMAP_GRADIENT,
            min_opacity=0.2,
            max_opacity=0.75,
            radius=18,
            blur=14,
        ).add_to(m)

    m.get_root().html.add_child(
        folium.Element(build_legend_html("RSSI Prédit (dBm)"))
    )
    return m


# ╔══════════════════════════════════════════════════════════════╗
# ║  UI — SIDEBAR                                               ║
# ╚══════════════════════════════════════════════════════════════╝

def render_sidebar(gateways_df: pd.DataFrame) -> str | None:
    """Render the sidebar controls and return the selected gateway ID."""
    st.sidebar.image(
        "https://img.icons8.com/fluency/96/radio-tower.png",
        width=64,
    )
    st.sidebar.title("📡 Contrôle")
    st.sidebar.markdown("---")

    # Gateway selector
    gw_list = ["__all__"] + sorted(gateways_df["gateway"].unique().tolist())
    gw_labels = ["🔽 Toutes les Gateways"] + [
        f"🛰 {gw[:18]}…" if len(gw) > 18 else f"🛰 {gw}"
        for gw in gw_list[1:]
    ]
    label_map = dict(zip(gw_list, gw_labels))

    selected = st.sidebar.selectbox(
        "Sélectionner une Gateway",
        options=gw_list,
        format_func=lambda x: label_map[x],
        index=0,
    )

    # Technical info for selected gateway
    if selected and selected != "__all__":
        gw_row = gateways_df[gateways_df["gateway"] == selected].iloc[0]
        st.sidebar.markdown("---")
        st.sidebar.markdown("### 🏗 Caractéristiques")
        col1, col2 = st.sidebar.columns(2)
        with col1:
            st.metric("Latitude", f"{gw_row['gw_lat']:.5f}°")
            st.metric("Altitude", f"{gw_row['gw_elevation']} m")
        with col2:
            st.metric("Longitude", f"{gw_row['gw_lon']:.5f}°")
            st.metric("Portée", f"{gw_row['range']:.0f} m")

    # RSSI legend in sidebar
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🎨 Légende RSSI")
    for color, label in zip(RSSI_COLORS_HEX, RSSI_LABELS):
        st.sidebar.markdown(
            f"<div style='display:flex;align-items:center;margin:3px 0;'>"
            f"<span style='background:{color};width:16px;height:16px;"
            f"display:inline-block;margin-right:8px;border-radius:3px;"
            f"border:1px solid #555;'></span>"
            f"<span style='font-size:13px;'>{label}</span>"
            f"</div>",
            unsafe_allow_html=True,
        )

    # Performance note
    st.sidebar.markdown("---")
    st.sidebar.caption(
        "💡 Les données et prédictions sont mises en cache. "
        "Le changement de filtre est instantané."
    )

    return selected if selected != "__all__" else None


# ╔══════════════════════════════════════════════════════════════╗
# ║  MAIN APP                                                  ║
# ╚══════════════════════════════════════════════════════════════╝

def main() -> None:
    # ── Load all data ───────────────────────────────────────
    with st.spinner("Chargement des données…"):
        gateways_df = load_gateways()
        coverage_df = load_coverage()
        ref_df = load_reference_points()
        # Predictor is loaded lazily (only when Map 2 is needed)

    # ── Sidebar ─────────────────────────────────────────────
    selected_gw = render_sidebar(gateways_df)

    # ── Title ───────────────────────────────────────────────
    st.title("📡 Wireless Coverage Prediction — Da Nang")
    st.markdown(
        "Dashboard de visualisation de la couverture réseau LoRaWAN. "
        "Utilisez le filtre latéral pour isoler une gateway spécifique."
    )

    # ══════════════════════════════════════════════════════════
    # MAP 1 — Historical / observed data
    # ══════════════════════════════════════════════════════════
    st.subheader("🗺️ Carte 1 — Couverture Historique (Observée)")
    st.caption(
        "Heatmap générée à partir des données réelles de `coverage.csv` "
        + (
            f" — filtrée par la gateway **{selected_gw}**"
            if selected_gw
            else " — toutes les gateways"
        )
    )

    with st.container():
        hist_map = build_historical_map(
            gateways_df, coverage_df, ref_df, selected_gw
        )
        st_folium(hist_map, width=None, height=500, key=f"map_hist_{selected_gw or 'all'}")

    # ══════════════════════════════════════════════════════════
    # MAP 2 — Predictive heatmap
    # ══════════════════════════════════════════════════════════
    st.subheader("🧠 Carte 2 — Heatmap Prédictive (ML Extra-Trees)")
    st.caption(
        "Grille de prédiction interpolée (pas de "
        f"{GRID_STEP}°). "
        + (
            f" Filtrage pour la gateway **{selected_gw}**."
            if selected_gw
            else " Toutes les gateways."
        )
    )

    with st.container():
        pred_map = build_predictive_map(
            gateways_df, coverage_df, selected_gw
        )
        st_folium(pred_map, width=None, height=500, key=f"map_pred_{selected_gw or 'all'}")

    # ── Summary stats ───────────────────────────────────────
    st.markdown("---")
    st.subheader("📊 Statistiques de couverture")
    cov_filtered = coverage_df.copy()
    if selected_gw:
        cov_filtered = cov_filtered[cov_filtered["gateway"] == selected_gw]

    if len(cov_filtered) > 0:
        rssi_vals = cov_filtered["rssi"][cov_filtered["rssi"] > -130]
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Points de mesure", len(cov_filtered))
        with col2:
            st.metric(
                "RSSI Moyen",
                f"{rssi_vals.mean():.1f} dBm" if len(rssi_vals) > 0 else "N/A",
            )
        with col3:
            st.metric(
                "RSSI Min",
                f"{rssi_vals.min():.1f} dBm" if len(rssi_vals) > 0 else "N/A",
            )
        with col4:
            st.metric(
                "RSSI Max",
                f"{rssi_vals.max():.1f} dBm" if len(rssi_vals) > 0 else "N/A",
            )
    else:
        st.info("Aucune donnée de couverture pour la sélection actuelle.")


# ╔══════════════════════════════════════════════════════════════╗
# ║  ENTRY POINT                                               ║
# ╚══════════════════════════════════════════════════════════════╝

if __name__ == "__main__":
    main()
