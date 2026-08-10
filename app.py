"""
Wireless Coverage Prediction — Interactive Dashboard
====================================================
Streamlit-based web application showing the LoRaWAN RSSI coverage of
Da Nang as a **discrete spatial-interpolation map** rendered with
Matplotlib + Contextily on an OpenStreetMap basemap:

  - coverage grid from ``coverage.csv`` (pcolormesh for regular grids,
    scipy ``griddata`` interpolation otherwise),
  - strict discrete RSSI thresholds (BoundaryNorm + ListedColormap),
  - gateways as black triangles (▲),
  - vertical colorbar "Predicted RSSI (dBm)".

Usage:
    streamlit run app.py
"""

from __future__ import annotations

import os
import sys

import numpy as np
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import geopandas as gpd
import contextily as ctx
from matplotlib.colors import BoundaryNorm, ListedColormap
from matplotlib.lines import Line2D
from scipy.interpolate import griddata

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

# HTTP headers for the OSM tile server (its usage policy blocks requests
# with a generic library User-Agent — see https://operations.osmfoundation.org/policies/tiles/)
TILE_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/126.0 Safari/537.36"
    ),
    "Referer": "http://localhost:8501/",
}

# Interpolation mesh resolution (cells per axis) for griddata
INTERP_RESOLUTION = 400

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


def _project_to_mercator(
    lats: np.ndarray, lons: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    """Project lat/lon arrays to Web-Mercator (EPSG:3857) x/y arrays."""
    gdf = gpd.GeoDataFrame(
        geometry=gpd.points_from_xy(lons, lats), crs="EPSG:4326"
    ).to_crs(epsg=3857)
    return gdf.geometry.x.values, gdf.geometry.y.values


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
    ref_df: pd.DataFrame,
    selected_gw: str | None = None,
) -> plt.Figure:
    """Build the RSSI coverage map (Matplotlib + Contextily).

    Renders ``coverage.csv`` as a discrete interpolation map on an OSM
    basemap:
      - full regular grid        → ``pcolormesh`` (no interpolation),
      - sparse / filtered subset → ``scipy.interpolate.griddata`` + ``imshow``,
    with the strict discrete palette (BoundaryNorm), ▲ gateway markers,
    a "Predicted RSSI (dBm)" colorbar and OSM attribution.

    When a single gateway is selected, its observed reference points
    (``reference_points.csv``) are overlaid as coloured dots so the
    covered area stays visible even if the gateway has no ``coverage.csv``
    grid rows.
    """
    cov = coverage_df.copy()
    if selected_gw:
        cov = cov[cov["gateway"] == selected_gw]

    # Out-of-range sentinel → rendered as the weakest (blue) class
    cov.loc[cov["rssi"] == OOD_RSSI_VALUE, "rssi"] = OOD_RSSI_DISPLAY

    # Observed reference points for the selected gateway (small dots).
    # Kept unfiltered so gateways whose coverage lies outside the Da Nang
    # bbox (e.g. other regions in gateways.csv) still display their points.
    ref_pts = pd.DataFrame()
    if selected_gw and ref_df is not None and len(ref_df) > 0:
        ref_pts = ref_df[ref_df["gateway"] == selected_gw].copy()
        # Sample to avoid clutter on very dense gateways
        if len(ref_pts) > 2000:
            ref_pts = ref_pts.sample(n=2000, random_state=42)

    fig, ax = plt.subplots(figsize=(10, 8))

    if len(cov) > 0:
        lats = np.sort(cov["lat"].unique())
        lons = np.sort(cov["lon"].unique())

        if _is_regular_grid(cov):
            # ── Regular grid → pcolormesh (no interpolation) ──
            z = (
                cov.sort_values(["lat", "lon"])["rssi"]
                .values.reshape(len(lats), len(lons))
            )
            lon2d, lat2d = np.meshgrid(lons, lats)
            x, y = _project_to_mercator(lat2d.ravel(), lon2d.ravel())
            im = ax.pcolormesh(
                x.reshape(lat2d.shape),
                y.reshape(lat2d.shape),
                z,
                cmap=RSSI_CMAP,
                norm=RSSI_NORM,
                alpha=0.6,
                zorder=2,
            )
        else:
            # ── Sparse / filtered data → griddata interpolation ──
            x, y = _project_to_mercator(cov["lat"].values, cov["lon"].values)
            z = cov["rssi"].values
            grid_x = np.linspace(x.min(), x.max(), INTERP_RESOLUTION)
            grid_y = np.linspace(y.min(), y.max(), INTERP_RESOLUTION)
            grid_x, grid_y = np.meshgrid(grid_x, grid_y)
            grid_z = griddata((x, y), z, (grid_x, grid_y), method="linear")
            im = ax.imshow(
                grid_z.T,
                extent=(x.min(), x.max(), y.min(), y.max()),
                origin="lower",
                cmap=RSSI_CMAP,
                norm=RSSI_NORM,
                alpha=0.6,
                interpolation="bilinear",
                zorder=2,
            )

        x_min, x_max = x.min(), x.max()
        y_min, y_max = y.min(), y.max()
        if len(ref_pts) > 0:
            # Keep observed points inside the view too
            rx, ry = _project_to_mercator(ref_pts["lat"].values, ref_pts["lon"].values)
            x_min = min(x_min, rx.min())
            x_max = max(x_max, rx.max())
            y_min = min(y_min, ry.min())
            y_max = max(y_max, ry.max())
    elif len(ref_pts) > 0:
        # No grid rows but observed points exist → zoom on them
        rx, ry = _project_to_mercator(ref_pts["lat"].values, ref_pts["lon"].values)
        x_min, x_max, y_min, y_max = rx.min(), rx.max(), ry.min(), ry.max()
        im = None
    else:
        # Nothing at all → fall back to the Da Nang bbox
        bb_lons = np.array([LON_MIN, LON_MIN, LON_MAX, LON_MAX])
        bb_lats = np.array([LAT_MIN, LAT_MAX, LAT_MIN, LAT_MAX])
        bb_x, bb_y = _project_to_mercator(bb_lats, bb_lons)
        x_min, x_max, y_min, y_max = bb_x.min(), bb_x.max(), bb_y.min(), bb_y.max()
        im = None

    # Small margin around the data extent
    mx = 0.02 * (x_max - x_min)
    my = 0.02 * (y_max - y_min)
    ax.set_xlim(x_min - mx, x_max + mx)
    ax.set_ylim(y_min - my, y_max + my)

    # ── OpenStreetMap basemap (Web-Mercator coordinates) ────────
    # Limits are set first so contextily infers a valid zoom level.
    ctx.add_basemap(
        ax,
        source=ctx.providers.OpenStreetMap.Mapnik,
        crs="EPSG:3857",
        headers=TILE_HEADERS,
        zorder=1,
        attribution="(C) OpenStreetMap contributors",
    )

    # ── Observed coverage points of the selected gateway ────────
    if len(ref_pts) > 0:
        rx, ry = _project_to_mercator(ref_pts["lat"].values, ref_pts["lon"].values)
        ax.scatter(
            rx, ry,
            s=18,
            c=[rssi_to_color(r) for r in ref_pts["rssi"].values],
            edgecolors="black",
            linewidth=0.3,
            alpha=0.85,
            zorder=3,
            label="Coverage points",
        )

    # ── Gateways as black triangles (▲) ─────────────────────────
    if selected_gw:
        # Always show the selected gateway's triangle, even outside the
        # Da Nang bbox (e.g. gateways from other regions in gateways.csv).
        gw = gateways_df[gateways_df["gateway"] == selected_gw].drop_duplicates(
            subset="gateway"
        )
    else:
        gw = gateways_df[
            gateways_df["gw_lat"].between(LAT_MIN, LAT_MAX)
            & gateways_df["gw_lon"].between(LON_MIN, LON_MAX)
        ].drop_duplicates(subset="gateway")
    if len(gw) > 0:
        gx, gy = _project_to_mercator(gw["gw_lat"].values, gw["gw_lon"].values)
        ax.scatter(
            gx, gy,
            marker="^",
            s=120,
            c="black",
            edgecolors="black",
            linewidth=1.5,
            zorder=5,
        )

    # ── Legend (▲ Gateway / Coverage points) — bottom-left ──────
    legend_handles = [
        Line2D(
            [0], [0],
            marker="^",
            linestyle="None",
            markersize=11,
            markerfacecolor="black",
            markeredgecolor="black",
            label="Gateway",
        )
    ]
    if len(ref_pts) > 0:
        legend_handles.append(
            Line2D(
                [0], [0],
                marker="o",
                linestyle="None",
                markersize=7,
                markerfacecolor="#888888",
                markeredgecolor="black",
                label="Coverage points",
            )
        )
    ax.legend(
        handles=legend_handles,
        loc="lower left",
        bbox_to_anchor=(0.0, 0.05),
        frameon=True,
        facecolor="white",
        edgecolor="#cccccc",
        fontsize=11,
    )

    # ── Title & axis cleanup ────────────────────────────────────
    ax.set_title("RSSI coverage in Da Nang", fontsize=14)
    ax.set_axis_off()

    # ── Colorbar (vertical, right) ──────────────────────────────
    # Always rendered (even with no mesh) so the palette stays readable.
    mappable = im if im is not None else plt.cm.ScalarMappable(
        norm=RSSI_NORM, cmap=RSSI_CMAP
    )
    cbar = fig.colorbar(
        mappable, ax=ax, ticks=[-120, -115, -110, -105, -100], shrink=0.85
    )
    cbar.set_label("Predicted RSSI (dBm)", fontsize=12)
    cbar.ax.tick_params(labelsize=10)

    fig.tight_layout()
    return fig


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
    # MAP — RSSI coverage (discrete spatial interpolation)
    # ══════════════════════════════════════════════════════════
    st.subheader("🗺️ Carte de Couverture RSSI — Interpolation Spatiale")
    st.caption(
        "Grille d'interpolation discrète (seuils stricts) sur fond OpenStreetMap, "
        "rendue avec Matplotlib + Contextily. "
        + (
            f" Filtrage pour la gateway **{selected_gw}**."
            if selected_gw
            else " Toutes les gateways."
        )
    )

    with st.container():
        fig = build_coverage_map(gateways_df, coverage_df, ref_df, selected_gw)
        st.pyplot(fig, use_container_width=True)

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
