import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import contextily as ctx

PREDICT=False
# --------------------
# Da Nang bounds
# --------------------

LAT_MIN = 15.87
LAT_MAX = 16.12

LON_MIN = 108.08
LON_MAX = 108.32

if(PREDICT):
    STEP = 0.1   # ~500 m
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
            rssi = predictor.predict(lat, lon)
            count += 1
            percent = count / total * 100
            print(f"[{count}/{total}] {percent:.1f}% - Predicted RSSI at ({lat:.4f}, {lon:.4f}): {rssi:.2f} dBm")
            points.append({"lat": lat, "lon": lon, "rssi": rssi})

    df = pd.DataFrame(points)
    df.to_csv("./data/predicted_coverage.csv", index=False)

df = pd.read_csv("./data/predicted_coverage.csv")
df_pred = pd.read_csv("./data/predicted_test_points.csv")
df_pred2 = pd.read_csv("./data/predicted_test_points2.csv")
df_pred["abs_error"] = (
    df_pred["rssi_true"] - df_pred["rssi_pred"]
).abs()
df_pred2["abs_error"] = (
    df_pred2["rssi_true"] - df_pred2["rssi_pred"]
).abs()

df_pred2 = (
    df_pred2.loc[
        df_pred2.groupby(["lat", "lon"])["abs_error"].idxmin()
    ]
    .reset_index(drop=True)
)

df_pred2 = df_pred2[~(df_pred2["gateway"]=="7276ff000b031aec")].copy()

print("MAE pred2: {:.2f} dB".format(df_pred2["abs_error"].mean()))
print("RMSE pred2: {:.2f} dB".format(np.sqrt((df_pred2["abs_error"] ** 2).mean())))


print("5 worst pred 2:")
print(df_pred2.nlargest(5, "abs_error"))


print("Number of test points (pred2): {}".format(df_pred2.__len__()))
# Filter to Da Nang bounds
df_pred = df_pred2.copy()

df_danang = df[
    (df['lat'] >= LAT_MIN) & (df['lat'] <= LAT_MAX) &
    (df['lon'] >= LON_MIN) & (df['lon'] <= LON_MAX)
].copy()

gdf = gpd.GeoDataFrame(
    df_danang,
    geometry=gpd.points_from_xy(df_danang["lon"], df_danang["lat"]),
    crs="EPSG:4326"
).to_crs(epsg=3857)

df_pred_danang = df_pred[
    (df_pred['lat'] >= LAT_MIN) & (df_pred['lat'] <= LAT_MAX) &
    (df_pred['lon'] >= LON_MIN) & (df_pred['lon'] <= LON_MAX)
].copy()

gdf_pred = gpd.GeoDataFrame(
    df_pred_danang,
    geometry=gpd.points_from_xy(df_pred_danang["lon"], df_pred_danang["lat"]),
    crs="EPSG:4326"
).to_crs(epsg=3857)

gdf_pred["error"] = (
    gdf_pred["rssi_true"] - gdf_pred["rssi_pred"]
).abs()

# =============================================================================
# Plot 1 : Predicted coverage only
# =============================================================================

fig, ax = plt.subplots(figsize=(12, 10))

gdf.plot(
    ax=ax,
    column="rssi",
    cmap="RdYlGn",
    markersize=15,
    alpha=0.8,
    legend=True
)

ctx.add_basemap(
    ax,
    source=ctx.providers.OpenStreetMap.Mapnik
)

ax.set_title("Predicted RSSI Coverage - Da Nang")

plt.show()

# =============================================================================
# Plot 2 : Prediction errors only
# =============================================================================

fig, ax = plt.subplots(figsize=(12, 10))

sc = ax.scatter(
    gdf_pred.geometry.x,
    gdf_pred.geometry.y,
    c=gdf_pred["error"],
    cmap="Reds",
    s=60,
    alpha=0.8,
    edgecolor="darkred",
    linewidth=1
)

ctx.add_basemap(
    ax,
    source=ctx.providers.OpenStreetMap.Mapnik
)

cbar = plt.colorbar(sc, ax=ax, fraction=0.036, pad=0.04)
cbar.set_label("Absolute error (dB)")

ax.set_title("Prediction Error on Test Points - Da Nang")

plt.show()

# =============================================================================
# Plot 3 : Hexbin coverage
# =============================================================================

fig, ax = plt.subplots(figsize=(12, 10))

gdf_all = gpd.GeoDataFrame(
    df,
    geometry=gpd.points_from_xy(df["lon"], df["lat"]),
    crs="EPSG:4326"
).to_crs(epsg=3857)

hb = ax.hexbin(
    gdf_all.geometry.x,
    gdf_all.geometry.y,
    C=gdf_all["rssi"],
    gridsize=40,
    alpha=0.8,
    reduce_C_function=np.mean,
    cmap="RdYlGn",
    mincnt=1
)

ctx.add_basemap(
    ax,
    source=ctx.providers.OpenStreetMap.Mapnik
)

cbar = plt.colorbar(hb, ax=ax)
cbar.set_label("Predicted RSSI (dBm)")

ax.set_title("Hexbin Predicted RSSI Coverage")

plt.show()