"""
Wireless Coverage Prediction — Interactive Dashboard
====================================================
Streamlit-based web application showing the LoRaWAN RSSI coverage of
Da Nang on **interactive Folium maps** (zoom / pan / tooltips), with the
surfaces rendered as image overlays on an OpenStreetMap basemap:

  - **all gateways** → discrete spatial-interpolation map (scipy
    ``griddata``; strict discrete RSSI thresholds via BoundaryNorm +
    ListedColormap),
  - **single gateway** → heatmap on a continuous colour scale covering
    the **whole view** (weakest blue where there is no data): predicted
    RSSI when a ``coverage.csv`` grid exists, otherwise interpolated from
    the observed measurement points (``reference_points.csv``); observed
    points stay overlaid inside and the gateway ▲ is always kept in view,
  - gateways as black triangles (▲),
  - colour scale widget ("Predicted RSSI (dBm)") on each map.

Usage:
    streamlit run app.py
"""

from __future__ import annotations

import os
import sys

import base64
import io

import numpy as np
import pandas as pd
import streamlit as st
import folium
from branca.colormap import LinearColormap, StepColormap
from matplotlib import image as mplimage
from matplotlib.colors import BoundaryNorm, ListedColormap, LinearSegmentedColormap, Normalize
from scipy.interpolate import griddata
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

# Da Nang bounding box (from plot.py + coverage.csv inspection)
LAT_MIN, LAT_MAX = 15.87, 16.12
LON_MIN, LON_MAX = 108.08, 108.32

OOD_RSSI_VALUE = -120.0   # out-of-range sentinel in coverage.csv
OOD_RSSI_DISPLAY = -130.0  # how the sentinel is rendered (weakest → blue class)

# Interpolation mesh resolution (cells per axis) for griddata
INTERP_RESOLUTION = 400

# ── Interactive map (Folium) settings ───────────────────────────
MAP_HEIGHT = 600                  # st_folium height in pixels
MAX_POINTS_ON_MAP = 400           # observed points per gateway (folium perf)

# ── Discrete RSSI palette (strict thresholds, weak → strong) ────
#  < -120 dBm : Bleu/Violet clair  #8899DD
#  -120 à -115: Cyan               #88FFFF
#  -115 à -110: Vert               #88D988
#  -110 à -105: Jaune              #FFFF88
#  -105 à -100: Orange             #FFCC88
#  > -100 dBm : Rouge clair        #FF8888
RSSI_COLORS_HEX = ["#8899DD", "#88FFFF", "#88D988", "#FFFF88", "#FFCC88", "#FF8888"]
RSSI_LABELS = [
    "< -120 dBm  (Faible)",
    "-120 à -115 dBm",
    "-115 à -110 dBm",
    "-110 à -105 dBm",
    "-105 à -100 dBm",
    "> -100 dBm  (Fort)",
]
RSSI_BOUNDS = [-120, -115, -110, -105, -100]

RSSI_CMAP = ListedColormap(RSSI_COLORS_HEX)
RSSI_NORM = BoundaryNorm(RSSI_BOUNDS, RSSI_CMAP.N, extend="both")

# ── Continuous "heatmap" scale for single-gateway maps ──────────
# Same palette as above but rendered as a smooth gradient. A fixed
# vmin/vmax keeps every gateway map on the same comparable scale.
RSSI_HEAT_CMAP = LinearSegmentedColormap.from_list("rssi_heat", RSSI_COLORS_HEX)
HEAT_VMIN, HEAT_VMAX = -130.0, -90.0
HEAT_NORM = Normalize(vmin=HEAT_VMIN, vmax=HEAT_VMAX)


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
    """Load reference (observed) points CSV from config.yaml path."""
    df = pd.read_csv(REFERENCE_PATH)
    df.columns = df.columns.str.strip()
    return df


# ╔══════════════════════════════════════════════════════════════╗
# ║  HELPER FUNCTIONS                                           ║
# ╚══════════════════════════════════════════════════════════════╝

def rssi_to_color(rssi: float) -> str:
    """Return the discrete hex colour for a given RSSI value (spec palette)."""
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


def _surface_to_data_uri(
    grid_z: np.ndarray,
    cmap,
    norm,
    alpha: float | None = None,
) -> str:
    """Encode a 2D value array as a transparent PNG data-URI for folium."""
    # No-data pixels (NaN) must stay transparent so the basemap shows through.
    transparent = np.isnan(grid_z)
    rgba = np.asarray(np.ma.filled(cmap(norm(grid_z)), 0.0))
    rgba = np.clip(rgba, 0.0, 1.0)
    if alpha is not None:
        rgba[..., 3] = alpha
    rgba[transparent, 3] = 0.0
    # Row 0 of the array is the southernmost latitude; image overlays anchor
    # the PNG's top edge on the north bound → flip vertically before encoding.
    rgba = np.flipud(rgba)
    buf = io.BytesIO()
    mplimage.imsave(buf, rgba, format="png")
    buf.seek(0)
    return "data:image/png;base64," + base64.b64encode(buf.read()).decode("ascii")


def _initial_zoom(lat_span: float) -> int:
    """Map zoom so a ~0.25° span (Da Nang bbox) is shown at zoom 12."""
    z = int(round(12 - np.log2(max(lat_span, 1e-4) / 0.25)))
    return int(min(17, max(8, z)))


def _folium_map(lat_min: float, lat_max: float, lon_min: float, lon_max: float) -> folium.Map:
    """Create a Folium map centred on the given lat/lon bounds."""
    return folium.Map(
        location=[(lat_min + lat_max) / 2, (lon_min + lon_max) / 2],
        zoom_start=_initial_zoom(lat_max - lat_min),
        tiles="OpenStreetMap",
        control_scale=True,
    )


def _is_regular_grid(df: pd.DataFrame) -> bool:
    """Return True when *df* samples a full, evenly-spaced lat/lon grid."""
    lats = np.sort(df["lat"].unique())
    lons = np.sort(df["lon"].unique())
    if len(lats) < 2 or len(lons) < 2:
        return False
    if len(lats) * len(lons) != len(df):
        return False
    lat_steps = np.diff(lats)
    lon_steps = np.diff(lons)
    return bool(
        np.allclose(lat_steps, lat_steps[0]) and np.allclose(lon_steps, lon_steps[0])
    )


def build_coverage_map(
    gateways_df: pd.DataFrame,
    coverage_df: pd.DataFrame,
) -> folium.Map:
    """Build the interactive all-gateways RSSI coverage map (Folium).

    Renders ``coverage.csv`` for **all** Da Nang gateways as a discrete
    spatial-interpolation surface (scipy ``griddata``, strict discrete RSSI
    thresholds via BoundaryNorm + ListedColormap) overlaid on an
    OpenStreetMap basemap, with ▲ gateway markers and a discrete colour
    scale. Fully interactive: zoom, pan, tooltips.

    This is the global view shown when no gateway is selected in the
    sidebar — the per-gateway view is handled by ``build_gateway_heatmap``.
    """
    cov = coverage_df.copy()

    # Out-of-range sentinel → rendered as the weakest (blue) class
    cov.loc[cov["rssi"] == OOD_RSSI_VALUE, "rssi"] = OOD_RSSI_DISPLAY

    # ── Interpolated surface (discrete classes) ────────────────
    surface_uri = None
    surface_bounds = None
    if len(cov) > 0:
        if _is_regular_grid(cov):
            lats = np.sort(cov["lat"].unique())
            lons = np.sort(cov["lon"].unique())
            grid_z = (
                cov.sort_values(["lat", "lon"])["rssi"]
                .values.reshape(len(lats), len(lons))
            )
            surface_bounds = [[lats.min(), lons.min()], [lats.max(), lons.max()]]
        else:
            x = cov["lon"].values
            y = cov["lat"].values
            z = cov["rssi"].values
            grid_lon = np.linspace(x.min(), x.max(), INTERP_RESOLUTION)
            grid_lat = np.linspace(y.min(), y.max(), INTERP_RESOLUTION)
            grid_lon, grid_lat = np.meshgrid(grid_lon, grid_lat)
            grid_z = griddata((x, y), z, (grid_lon, grid_lat), method="linear")
            surface_bounds = [[y.min(), x.min()], [y.max(), x.max()]]
        surface_uri = _surface_to_data_uri(grid_z, RSSI_CMAP, RSSI_NORM, alpha=0.6)

    # ── View bounds: surface ∪ gateways (Da Nang) ──────────────
    lats = [LAT_MIN, LAT_MAX]
    lons = [LON_MIN, LON_MAX]
    if surface_bounds is not None:
        lats = [surface_bounds[0][0], surface_bounds[1][0]]
        lons = [surface_bounds[0][1], surface_bounds[1][1]]
    gw = gateways_df[
        gateways_df["gw_lat"].between(LAT_MIN, LAT_MAX)
        & gateways_df["gw_lon"].between(LON_MIN, LON_MAX)
    ].drop_duplicates(subset="gateway")
    if len(gw) > 0:
        lats += [gw["gw_lat"].min(), gw["gw_lat"].max()]
        lons += [gw["gw_lon"].min(), gw["gw_lon"].max()]

    m = _folium_map(min(lats), max(lats), min(lons), max(lons))

    # ── Surface overlay (NaN stays transparent → basemap visible) ─
    if surface_uri is not None and surface_bounds is not None:
        folium.raster_layers.ImageOverlay(
            image=surface_uri,
            bounds=surface_bounds,
        ).add_to(m)

    # ── Gateways (Da Nang) as black triangles (▲) ───────────────
    for _, row in gw.iterrows():
        folium.RegularPolygonMarker(
            location=[row["gw_lat"], row["gw_lon"]],
            number_of_sides=3,
            radius=9,
            color="black",
            weight=1.5,
            fill=True,
            fill_color="black",
            fill_opacity=1.0,
            tooltip=row["gateway"],
        ).add_to(m)

    # ── Discrete colour scale (matches the sidebar legend) ──────
    StepColormap(
        colors=RSSI_COLORS_HEX,
        index=RSSI_BOUNDS,
        vmin=-120,
        vmax=-100,
        caption="Predicted RSSI (dBm)",
    ).add_to(m)

    return m


def build_gateway_heatmap(
    gateways_df: pd.DataFrame,
    coverage_df: pd.DataFrame,
    ref_df: pd.DataFrame,
    selected_gw: str,
) -> folium.Map:
    """Build an interactive RSSI heatmap for a selected gateway.

    The heatmap is interpolated over the **whole view** on a continuous
    colour scale: areas without any data are filled with the weakest blue
    class so it always covers the entire visible map.

    Data source priority:
      1. predicted grid (``coverage.csv``) → "RSSI prédit" heatmap;
      2. otherwise, the observed measurement points
         (``reference_points.csv``) → "RSSI observé" heatmap.

    Observed measurement points stay visible inside as coloured dots, and
    the gateway ▲ is always kept in the view.
    """
    # ── Predicted grid rows for this gateway ─────────────────────
    cov = coverage_df[coverage_df["gateway"] == selected_gw].copy()
    # Out-of-range sentinel → rendered as the weakest (blue) class
    cov.loc[cov["rssi"] == OOD_RSSI_VALUE, "rssi"] = OOD_RSSI_DISPLAY

    # ── Observed measurement points (reference_points.csv) ──────
    ref_all = pd.DataFrame()
    if ref_df is not None and len(ref_df) > 0:
        ref_all = ref_df[ref_df["gateway"] == selected_gw].copy()
        ref_all = ref_all.dropna(subset=["lat", "lon", "rssi"])
    ref_pts = ref_all.copy()
    if len(ref_pts) > MAX_POINTS_ON_MAP:  # keep the Folium map responsive
        ref_pts = ref_pts.sample(n=MAX_POINTS_ON_MAP, random_state=42)

    # ── Gateway position(s) — always kept in the view ───────────
    gw = gateways_df[gateways_df["gateway"] == selected_gw].drop_duplicates(
        subset="gateway"
    )

    # ── View bounds: predictions ∪ observed points ∪ gateway ────
    lats: list[float] = []
    lons: list[float] = []
    if len(cov) >= 4:
        lats += [cov["lat"].min(), cov["lat"].max()]
        lons += [cov["lon"].min(), cov["lon"].max()]
    if len(ref_all) > 0:
        lats += [ref_all["lat"].min(), ref_all["lat"].max()]
        lons += [ref_all["lon"].min(), ref_all["lon"].max()]
    if len(gw) > 0:
        lats += [gw["gw_lat"].min(), gw["gw_lat"].max()]
        lons += [gw["gw_lon"].min(), gw["gw_lon"].max()]

    if not lats:  # nothing at all → fall back to the Da Nang bbox
        lats, lons = [LAT_MIN, LAT_MAX], [LON_MIN, LON_MAX]

    lat_min, lat_max = min(lats), max(lats)
    lon_min, lon_max = min(lons), max(lons)
    m_lat = 0.05 * (lat_max - lat_min)
    m_lon = 0.05 * (lon_max - lon_min)
    lat_min -= m_lat
    lat_max += m_lat
    lon_min -= m_lon
    lon_max += m_lon

    # ── Heatmap interpolated over the FULL view (full coverage) ─
    # Priority: predicted grid → observed points.
    surface_uri = None
    scale_caption = "RSSI prédit (dBm)"
    heat_source = None
    if len(cov) >= 4:  # prediction grid available
        heat_source = (cov["lon"].values, cov["lat"].values, cov["rssi"].values)
    elif len(ref_all) >= 4:  # no prediction grid → observed heatmap
        heat_source = (
            ref_all["lon"].values,
            ref_all["lat"].values,
            ref_all["rssi"].values,
        )
        scale_caption = "RSSI observé (dBm)"
    if heat_source is not None:
        x, y, z = heat_source
        grid_lon = np.linspace(lon_min, lon_max, INTERP_RESOLUTION)
        grid_lat = np.linspace(lat_min, lat_max, INTERP_RESOLUTION)
        grid_lon, grid_lat = np.meshgrid(grid_lon, grid_lat)
        grid_z = griddata((x, y), z, (grid_lon, grid_lat), method="linear")
        # Full coverage: areas with no data → weakest blue
        grid_z = np.where(np.isnan(grid_z), HEAT_VMIN, grid_z)
        surface_uri = _surface_to_data_uri(
            grid_z, RSSI_HEAT_CMAP, HEAT_NORM, alpha=0.65
        )

    m = _folium_map(lat_min, lat_max, lon_min, lon_max)

    # ── Heatmap overlay covering the whole view ─────────────────
    if surface_uri is not None:
        folium.raster_layers.ImageOverlay(
            image=surface_uri,
            bounds=[[lat_min, lon_min], [lat_max, lon_max]],
        ).add_to(m)

    # ── Observed measurement points inside the heatmap ──────────
    for _, p in ref_pts.iterrows():
        color = rssi_to_color(p["rssi"])
        folium.CircleMarker(
            location=[p["lat"], p["lon"]],
            radius=3,
            weight=0.3,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.9,
            tooltip=f"RSSI observé : {p['rssi']:.0f} dBm",
        ).add_to(m)

    # ── Gateway as a black triangle (▲) ─────────────────────────
    for _, row in gw.iterrows():
        folium.RegularPolygonMarker(
            location=[row["gw_lat"], row["gw_lon"]],
            number_of_sides=3,
            radius=10,
            color="black",
            weight=1.5,
            fill=True,
            fill_color="black",
            fill_opacity=1.0,
            tooltip=selected_gw,
        ).add_to(m)

    # ── Continuous colour scale (heatmap) ───────────────────────
    if surface_uri is not None:
        LinearColormap(
            colors=RSSI_COLORS_HEX,
            vmin=HEAT_VMIN,
            vmax=HEAT_VMAX,
            caption=scale_caption,
        ).add_to(m)

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
        # Idempotent lookup: safe both in the app and under AppTest.
        format_func=lambda x: label_map.get(x, x),
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

    # ── Sidebar ─────────────────────────────────────────────
    selected_gw = render_sidebar(gateways_df)

    # ── Title ───────────────────────────────────────────────
    st.title("📡 Wireless Coverage Prediction — Da Nang")
    st.markdown(
        "Dashboard de visualisation de la couverture réseau LoRaWAN. "
        "Utilisez le filtre latéral pour isoler une gateway spécifique."
    )

    # ══════════════════════════════════════════════════════════
    # MAP — RSSI coverage (interactive Folium)
    # ══════════════════════════════════════════════════════════
    if selected_gw:
        # Same threshold as build_gateway_heatmap(): < 4 grid rows = no grid.
        has_prediction_grid = (
            len(coverage_df[coverage_df["gateway"] == selected_gw]) >= 4
        )
        has_observed_points = len(ref_df[ref_df["gateway"] == selected_gw]) > 0
        st.subheader("🗺️ Heatmap RSSI — Gateway Sélectionnée")
        if has_prediction_grid:
            st.caption(
                "**Heatmap prédictive** : interpolation continue du RSSI prédit "
                f"(grille `coverage.csv`) pour la gateway **{selected_gw}**. "
                "La heatmap couvre toute la carte (bleu = absence de signal "
                "prédit). Les points colorés sont les **mesures RSSI observées** "
                "(`reference_points.csv`). Le triangle noir ▲ marque la position "
                "de la gateway. 🖱 Carte interactive : zoom à la molette, "
                "déplacement en glissant."
            )
        elif has_observed_points:
            st.caption(
                "**Heatmap observée** : aucune grille de prédiction "
                f"(`coverage.csv`) pour la gateway **{selected_gw}** — la "
                "heatmap est interpolée à partir des **mesures RSSI observées** "
                "(`reference_points.csv`), les points d'origine restant "
                "affichés dessus. Le triangle noir ▲ marque la position de la "
                "gateway. 🖱 Carte interactive : zoom à la molette, "
                "déplacement en glissant."
            )
        else:
            st.caption(
                f"Aucune donnée (grille de prédiction ni points de mesure) "
                f"pour la gateway **{selected_gw}**. 🖱 Carte interactive : "
                "zoom à la molette, déplacement en glissant."
            )
    else:
        st.subheader("🗺️ Carte de Couverture RSSI — Toutes les Gateways")
        st.caption(
            "Interpolation spatiale discrète (seuils stricts) du RSSI prédit, "
            "sur fond OpenStreetMap. Les triangles noirs ▲ marquent les "
            "gateways de Da Nang. 🖱 Carte interactive : zoom à la molette, "
            "déplacement en glissant."
        )

    with st.container():
        if selected_gw:
            map_obj = build_gateway_heatmap(
                gateways_df, coverage_df, ref_df, selected_gw
            )
        else:
            map_obj = build_coverage_map(gateways_df, coverage_df)
        st_folium(map_obj, width="100%", height=MAP_HEIGHT)

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
