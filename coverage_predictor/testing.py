import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import contextily as ctx

import predictor


# --------------------
# Da Nang bounds
# --------------------

LAT_MIN = 15.87
LAT_MAX = 16.12

LON_MIN = 108.08
LON_MAX = 108.32

STEP = 0.05   # ~500 m

# --------------------
# Grid generation
# --------------------

points = []

for lat in np.arange(
    LAT_MIN,
    LAT_MAX,
    STEP
):

    for lon in np.arange(
        LON_MIN,
        LON_MAX,
        STEP
    ):

        rssi = predictor.predict(
            lat,
            lon
        )
        print(f"Predicted RSSI at ({lat:.4f}, {lon:.4f}): {rssi:.2f} dBm")
        points.append(
            {
                "lat": lat,
                "lon": lon,
                "rssi": rssi
            }
        )

df = pd.DataFrame(points)

print(df.head())

gdf = gpd.GeoDataFrame(
    df,
    geometry=gpd.points_from_xy(
        df["lon"],
        df["lat"]
    ),
    crs="EPSG:4326"
).to_crs(
    epsg=3857
)

fig, ax = plt.subplots(
    figsize=(12, 10)
)

gdf.plot(
    ax=ax,
    column="rssi",
    cmap="RdYlGn",
    markersize=15,
    alpha=0.8,
    legend=True,
)

ctx.add_basemap(
    ax,
    source=ctx.providers.OpenStreetMap.Mapnik
)

ax.set_title(
    "Predicted RSSI Coverage - Da Nang"
)

plt.show()

plt.figure(
    figsize=(12,10)
)

plt.hexbin(
    df["lon"],
    df["lat"],
    C=df["rssi"],
    gridsize=50,
    reduce_C_function=np.mean
)

plt.colorbar(
    label="Predicted RSSI (dBm)"
)

plt.title(
    "Predicted Coverage - Da Nang"
)

plt.show()