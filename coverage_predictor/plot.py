import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import contextily as ctx
from scipy.interpolate import griddata
from matplotlib.colors import ListedColormap, BoundaryNorm


PREDICT=False
# --------------------
# Da Nang bounds
# --------------------

LAT_MIN = 15.87
LAT_MAX = 16.12

LON_MIN = 108.08
LON_MAX = 108.32

if(PREDICT):
    STEP = 0.002  
    import predictor
    # --------------------
    # Grid generation
    # --------------------

    points = []
    lat_vals = np.arange(LAT_MIN, LAT_MAX, STEP)
    lon_vals = np.arange(LON_MIN, LON_MAX, STEP)

    total = len(lat_vals) * len(lon_vals)
    count = 0

    for lat in lat_vals:
        for lon in lon_vals:
            rssi = predictor.predict(lat, lon, gateway = "7276ff002e0507da", frequency = None, spreading_factor = 12)
            count += 1
            percent = count / total * 100
            print(f"[{count}/{total}] {percent:.1f}% - Predicted RSSI at ({lat:.4f}, {lon:.4f}): {rssi:.2f} dBm")
            points.append({"lat": lat, "lon": lon, "rssi": rssi})

    df = pd.DataFrame(points)
    df.to_csv("./data/coverage_one_gateway.csv", index=False)

df = pd.read_csv("./data/coverage.csv")


df_danang = df[
    (df['lat'] >= LAT_MIN) & (df['lat'] <= LAT_MAX) &
    (df['lon'] >= LON_MIN) & (df['lon'] <= LON_MAX)
].copy()


# Out-of-range predictions -> blue
df_danang.loc[
    df_danang["rssi"] == -120.0,
    "rssi"
] = -150.0

# Real RSSI values below -120 -> clamp to -120
df_danang.loc[
    (df_danang["rssi"] < -120.0) &
    (df_danang["rssi"] > -150.0),
    "rssi"
] = -119.0

# df_danang["rssi"] = df_danang["rssi"].clip(lower=-120, upper=0)
# ------------------------------------------------------------------
# Préparation des données
# ------------------------------------------------------------------

gdf = gpd.GeoDataFrame(
    df_danang,
    geometry=gpd.points_from_xy(df_danang["lon"], df_danang["lat"]),
    crs="EPSG:4326"
).to_crs(epsg=3857)

x = gdf.geometry.x.values
y = gdf.geometry.y.values
z = gdf["rssi"].values

# ------------------------------------------------------------------
# Préparation interpolation et affichage (plot unique)
# ------------------------------------------------------------------

cmap = ListedColormap([
    "#0047AB",  # Bleu
    "#00FFFF",  # Cyan
    "#00AA00",  # Vert
    "#FFFF00",  # Jaune
    "#FFA500",  # Orange
    "#FF0000",  # Rouge
])

bounds = [-130,-120, -115, -110, -105, -100, 0]

norm = BoundaryNorm(
    bounds,
    cmap.N
)

grid_x, grid_y = np.mgrid[
    x.min():x.max():400j,
    y.min():y.max():400j
]

grid_z = griddata(
    (x, y),
    z,
    (grid_x, grid_y),
    method="linear"      # essayer aussi "nearest" ou "cubic"
)

# ------------------------------------------------------------------
# Figure : Interpolation
# ------------------------------------------------------------------

fig, ax = plt.subplots(figsize=(7, 7))

x_margin = 0.02 * (x.max() - x.min())   # 5 %
y_margin = 0.02 * (y.max() - y.min())

im = ax.imshow(
    grid_z.T,
    extent=(x.min(), x.max(), y.min(), y.max()),
    origin="lower",
    cmap=cmap,
    norm=norm,
    alpha=0.42,
    interpolation="bilinear",
    zorder=2
)

ctx.add_basemap(
    ax,
    source=ctx.providers.OpenStreetMap.Mapnik,
    zorder=1
)
df_gw = pd.read_csv("./data/gateways.csv")
first = True
for _, row in gpd.GeoDataFrame(
    df_gw,
    geometry=gpd.points_from_xy(df_gw["gw_lon"], df_gw["gw_lat"]),
    crs="EPSG:4326"
).to_crs(epsg=3857).iterrows():
        ax.scatter(
            row.geometry.x,
            row.geometry.y,
            marker="^",
            s=110,
            alpha=0.8,
            color="black",
            edgecolor="white",
            linewidth=1.5,
            zorder=1,
            label="Gateway" if first else None
        )
        first = False

ax.legend(
    loc="lower left",
    frameon=True,
    facecolor="white"
)

ax.set_xlim(x.min() - x_margin, x.max() + x_margin)
ax.set_ylim(y.min() - y_margin, y.max() + y_margin)

cbar = fig.colorbar(
    im,
    ax=ax,
    boundaries=bounds,
    ticks=[-120, -115, -110, -105, -100]
)

cbar.set_label("Predicted RSSI (dBm)")

ax.set_title("RSSI coverage in Da Nang")
ax.set_axis_off()

plt.show()

#############################################################"
# 
# 



gateway_codes = {
    gw: i
    for i, gw in enumerate(sorted(gdf["gateway"].unique()))
}

gdf["gateway_id"] = gdf["gateway"].map(gateway_codes)

x = gdf.geometry.x.values
y = gdf.geometry.y.values
z = gdf["gateway_id"].values

# -------------------------------------------------------
# Interpolation
# -------------------------------------------------------

grid_x, grid_y = np.mgrid[
    x.min():x.max():500j,
    y.min():y.max():500j
]

grid_z = griddata(
    (x, y),
    z,
    (grid_x, grid_y),
    method="nearest"
)

# -------------------------------------------------------
# Gateways
# -------------------------------------------------------

gateways = pd.read_csv("./data/gateways.csv")

gateways = gateways[
    gateways["gateway"].isin(gateway_codes)
].copy()

gateways["gateway_id"] = gateways["gateway"].map(gateway_codes)

gw_gdf = gpd.GeoDataFrame(
    gateways,
    geometry=gpd.points_from_xy(
        gateways["gw_lon"],
        gateways["gw_lat"]
    ),
    crs="EPSG:4326"
).to_crs(epsg=3857)


# -------------------------------------------------------
# Plot
# -------------------------------------------------------


fig, ax = plt.subplots(figsize=(7, 7))

cmap = plt.cm.get_cmap(
    "tab20",
    len(gateway_codes)
)

im = ax.imshow(
    grid_z.T,
    extent=(x.min(), x.max(), y.min(), y.max()),
    origin="lower",
    cmap=cmap,
    interpolation="nearest",
    alpha=0.45,
    zorder=2
)

ctx.add_basemap(
    ax,
    source=ctx.providers.OpenStreetMap.Mapnik,
    zorder=1
)
first = True
# Gateways (same color as their area)
for _, row in gw_gdf.iterrows():

    color = cmap(row["gateway_id"])

    ax.scatter(
        row.geometry.x,
        row.geometry.y,
        marker="^",
        s=110,
        alpha=0.8,
        color=color,
        edgecolor="black",
        linewidth=1.5,
        zorder=4,
        label = "Gateway" if first else None
    )
    first = False

ax.legend(
    loc="lower left",
    frameon=True,
    facecolor="white"
)

margin = 0.02  # 5 %

dx = x.max() - x.min()
dy = y.max() - y.min()

ax.set_xlim(
    x.min() - margin * dx,
    x.max() + margin * dx
)

ax.set_ylim(
    y.min() - margin * dy,
    y.max() + margin * dy
)

ax.set_title("Selected gateway")
ax.set_axis_off()

plt.show()

from matplotlib.lines import Line2D
from matplotlib.patches import Patch

fig, ax = plt.subplots(figsize=(7, 7))

cmap = plt.cm.get_cmap("tab20", len(gateway_codes))

im = ax.imshow(
    grid_z.T,
    extent=(x.min(), x.max(), y.min(), y.max()),
    origin="lower",
    cmap=cmap,
    interpolation="nearest",
    alpha=0.45,
    zorder=2
)

ctx.add_basemap(
    ax,
    source=ctx.providers.OpenStreetMap.Mapnik,
    zorder=1
)

# Plot gateways
for _, row in gw_gdf.iterrows():

    color = cmap(row["gateway_id"])

    ax.scatter(
        row.geometry.x,
        row.geometry.y,
        marker="^",
        s=110,
        color=color,
        edgecolor="black",
        linewidth=1.5,
        alpha=0.9,
        zorder=4
    )

# Margins
margin = 0.02

dx = x.max() - x.min()
dy = y.max() - y.min()

ax.set_xlim(
    x.min() - margin * dx,
    x.max() + margin * dx
)

ax.set_ylim(
    y.min() - margin * dy,
    y.max() + margin * dy
)

# ---------- Legend ----------
legend_elements = [
    Patch(
        facecolor="lightgray",
        edgecolor="black",
        alpha=0.45,
        label="Selected gateway region"
    ),
    Line2D(
        [0], [0],
        marker="^",
        linestyle="",
        markersize=10,
        markerfacecolor="gray",
        markeredgecolor="black",
        label="Gateway"
    ),
]

ax.legend(
    handles=legend_elements,
    loc="lower left",
    frameon=True,
    facecolor="white"
)

ax.set_title("Selected gateway")
ax.set_axis_off()

plt.tight_layout()
plt.show()