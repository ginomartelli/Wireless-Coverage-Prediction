import pandas as pd


GATEWAY_COLUMNS = [
    "gateway",
    "gw_lat",
    "gw_lon",
    "gw_elevation",
]


def build_gateways_dataset(
    input_csv="../data/processed/data_with_closest_points_features.csv",
    output_csv="../data/processed/gateways.csv",
):

    df = pd.read_csv(input_csv)

    gateways_df = df[
        [
            "gateway",
            "gw_lat",
            "gw_lon",
            "gw_elevation",
        ]
    ].copy()

    # Quantification spatiale (~1 m avec 5 décimales)

    gateways_df["gw_lat_round"] = (
        gateways_df["gw_lat"]
        .round(0)
    )

    gateways_df["gw_lon_round"] = (
        gateways_df["gw_lon"]
        .round(0)
    )

    # On ne supprime que les vraies copies
    gateways_df = (
        gateways_df
        .drop_duplicates(
            subset=[
                "gateway",
                "gw_lat_round",
                "gw_lon_round",
            ]
        )
        .drop(
            columns=[
                "gw_lat_round",
                "gw_lon_round",
            ]
        )
        .sort_values(
            [
                "gateway",
                "gw_lat",
                "gw_lon",
            ]
        )
        .reset_index(drop=True)
    )

    ranges = (
        df.groupby("gateway")["distance"]
        .quantile(0.95)
    )

    gateways_df["range"] = gateways_df["gateway"].map(ranges)
    gateways_df.to_csv(output_csv, index=False)

    print(f"Saved {len(gateways_df)} gateways to {output_csv}")