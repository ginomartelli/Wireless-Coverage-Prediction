import sys
import os

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import contextily as ctx
import geopandas as gpd

# ── Configuration ──
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config_loader import config  # noqa: E402

from api.fetch_data import fetch_device_history
from processing.cleaning import clean_data
from processing.features import add_closest_point_features, add_basic_features, add_terrain_features
from processing.parser import parse_devices
from ml.predict import predict
from ml.train import train

from build_gateways_dataset import build_gateways_dataset
from build_reference_dataset import build_reference_dataset

TRN = config["paths"]["training"]
DATA_PATH = TRN["devices_history_csv"]
DATA_PATH_1 = TRN["devices_history_1_csv"]
DATA_PATH_2 = TRN["devices_history_2_csv"]

FORCE_FETCH = False
ADD_FEATURES = False
TRAIN =False
MODEL_TYPE = "extra_trees"
SHOW_PLOTS =False
SAVE_DATA_WITH_FEATURES =False
PREDICT = False
BUILD_REF = False
BUILD_GW = False

def main():
    if(os.path.exists(DATA_PATH) and not FORCE_FETCH):
        print("Loading local data...")
        df = pd.read_csv(DATA_PATH)
    else:
        if os.path.exists(DATA_PATH_1) and not FORCE_FETCH:
            print("Loading local data 1...")
            df = pd.read_csv(DATA_PATH_1)
        else:
            print("Fetching data 1 from API...")

            devices = ["board01", "node3", "node01"]
            all_data = []

            for d in devices:
                print(f"Fetching {d}...")
                data = fetch_device_history(d)
                all_data.extend(data)

            print("Parsing data...")
            df = parse_devices(all_data)
            df = clean_data(df)
            df.to_csv(DATA_PATH_1, index=False)
            print("Data 1 saved!")

        if(os.path.exists(DATA_PATH_2) and not FORCE_FETCH):
            print("Loading local data 2...")
            df2 = pd.read_csv(DATA_PATH_2)
        else:
            print("Fetching data 2 from API...")

            devices = ["board01", "node3", "node01"] # (only node01 for now)
            all_data = []

            for d in devices:
                print(f"Fetching {d}...")
                data = fetch_device_history(d, type=2)
                all_data.extend(data)

            print("Parsing data...")
            df2 = parse_devices(all_data)
            df2 = clean_data(df2)
            df2.to_csv(DATA_PATH_2, index=False)
            print("Data 2 saved!")
        df = pd.concat([df, df2], ignore_index=True)
        df = df.drop_duplicates()
        df.to_csv(DATA_PATH, index=False)
        print("Full data saved!")
        print(df.describe())
    if(ADD_FEATURES):
        print("Adding features...")
        # df = add_basic_features(df)
        
        # df = add_terrain_features(df)
        df = clean_data(df)
        df = df.drop_duplicates()
        df.to_csv(DATA_PATH, index=False)
        print("Features added and data saved!")

    if TRAIN:
        train(MODEL_TYPE)

    if SAVE_DATA_WITH_FEATURES:
        print("Adding features for predictions...")
        df_with_features = df.copy()
        df_with_features = add_closest_point_features(
            df_with_features,
            reference_df=df_with_features
        )
        df_with_features.to_csv(
            "../data/processed/data_with_closest_points_features.csv",
            index=False
        )
        print("Features added and data saved!")
    if BUILD_REF:
        print("Building reference dataset...")
        build_reference_dataset()
    if BUILD_GW:
        print("Building gateways dataset...")
        build_gateways_dataset()
    if(PREDICT or SHOW_PLOTS):
        print("Predicting...")
        df["predicted_rssi"] = predict(df, model_type=MODEL_TYPE, reference_df=df)
        df["error"] = df["rssi"] - df["predicted_rssi"]
        df["abs_error"] = np.abs(df["error"])

    if SHOW_PLOTS:

        print("Showing plots...")

        df_danang = df[df["lat"] < 18].copy()
        df_haiphong = df[df["lat"] > 18].copy()

        # =====================================================
        # DA NANG - POINTS
        # =====================================================

        gdf = gpd.GeoDataFrame(
            df_danang,
            geometry=gpd.points_from_xy(
                df_danang.lon,
                df_danang.lat
            ),
            crs="EPSG:4326"
        ).to_crs(epsg=3857)

        fig, ax = plt.subplots(
            figsize=(12, 10)
        )

        gdf.plot(
            ax=ax,
            column="abs_error",
            cmap="inferno",
            markersize=30,
            alpha=0.2,
            legend=True,
            vmin=0,
            vmax=8
        )

        gateways = (
            df_danang
            .groupby("gateway")
            .first()
            .reset_index()[
                ["gateway", "gw_lat", "gw_lon"]
            ]
        )

        gw_gdf = gpd.GeoDataFrame(
            gateways,
            geometry=gpd.points_from_xy(
                gateways.gw_lon,
                gateways.gw_lat
            ),
            crs="EPSG:4326"
        ).to_crs(epsg=3857)

        gw_gdf.plot(
            ax=ax,
            marker="^",
            color="green",
            markersize=80,
            alpha=0.7,
            label="Gateway"
        )

        ctx.add_basemap(
            ax,
            source=ctx.providers.OpenStreetMap.Mapnik
        )

        ax.legend()
        ax.set_title(
            "Da Nang RSSI Prediction Error"
        )

        ax.set_axis_off()

        plt.show()

        # =====================================================
        # DA NANG - HEXBIN
        # =====================================================

        fig, ax = plt.subplots(
            figsize=(12, 10)
        )

        hb = ax.hexbin(
            gdf.geometry.x,
            gdf.geometry.y,
            C=np.abs(df_danang["error"]),
            reduce_C_function=np.mean,
            gridsize=75,
            mincnt=1,
            vmax=4
        )

        gw_gdf.plot(
            ax=ax,
            marker="^",
            color="red",
            markersize=60,
            alpha=0.7,
            label="Gateway"
        )

        ctx.add_basemap(
            ax,
            source=ctx.providers.OpenStreetMap.Mapnik
        )

        cbar = plt.colorbar(
            hb,
            ax=ax
        )

        cbar.set_label(
            "Mean Absolute Error (dBm)"
        )

        ax.legend()

        ax.set_title(
            "Da Nang RSSI Prediction Error Heatmap"
        )

        ax.set_axis_off()

        plt.show()

        # =====================================================
        # HAI PHONG - POINTS
        # =====================================================

        gdf = gpd.GeoDataFrame(
            df_haiphong,
            geometry=gpd.points_from_xy(
                df_haiphong.lon,
                df_haiphong.lat
            ),
            crs="EPSG:4326"
        ).to_crs(epsg=3857)

        fig, ax = plt.subplots(
            figsize=(12, 10)
        )

        gdf.plot(
            ax=ax,
            column="abs_error",
            cmap="inferno",
            markersize=15,
            alpha=0.7,
            legend=True,
            vmin=0,
            vmax=8
        )

        gateways = (
            df_haiphong[
                ["gateway", "gw_lat", "gw_lon"]
            ]
            .drop_duplicates()
        )

        gw_gdf = gpd.GeoDataFrame(
            gateways,
            geometry=gpd.points_from_xy(
                gateways.gw_lon,
                gateways.gw_lat
            ),
            crs="EPSG:4326"
        ).to_crs(epsg=3857)

        gw_gdf.plot(
            ax=ax,
            marker="^",
            color="cyan",
            markersize=120,
            label="Gateway"
        )

        ctx.add_basemap(
            ax,
            source=ctx.providers.OpenStreetMap.Mapnik
        )

        ax.legend()

        ax.set_title(
            "Hai Phong RSSI Prediction Error"
        )

        ax.set_axis_off()

        plt.show()

        # =====================================================
        # HAI PHONG - HEXBIN
        # =====================================================

        fig, ax = plt.subplots(
            figsize=(12, 10)
        )

        hb = ax.hexbin(
            gdf.geometry.x,
            gdf.geometry.y,
            C=np.abs(df_haiphong["error"]),
            reduce_C_function=np.mean,
            gridsize=75,
            mincnt=1,
            vmax=4
        )

        gw_gdf.plot(
            ax=ax,
            marker="^",
            color="red",
            markersize=60,
            alpha=0.7,
            label="Gateway"
        )

        ctx.add_basemap(
            ax,
            source=ctx.providers.OpenStreetMap.Mapnik
        )

        cbar = plt.colorbar(
            hb,
            ax=ax
        )

        cbar.set_label(
            "Mean Absolute Error (dBm)"
        )

        ax.legend()

        ax.set_title(
            "Hai Phong RSSI Prediction Error Heatmap"
        )

        ax.set_axis_off()

        plt.show()


if __name__ == "__main__":
    main()
