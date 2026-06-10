import numpy as np
import pandas as pd

import predictor
import feature_builder


# ---------------------------------------
# Load validation dataset
# ---------------------------------------

df = pd.read_csv(
    "../data/processed/devices_history_full.csv"
)

# Pour aller plus vite pendant les tests :
df = df.sample(50, random_state=42)

# ---------------------------------------
# Predict
# ---------------------------------------

predictions = []

for i, row in df.iterrows():
    lat=row["lat"] + 1e-4,
    lon=row["lon"] + 1e-4,
    pred = predictor.predict(
        lat=lat[0],
        lon=lon[0],
        gateway=row["gateway"],
        frequency=row["frequency"],
        spreading_factor=row["spreading_factor"],
    )

    predictions.append(pred)

    if (i + 1) % 5 == 0:
        print(
            f"{(i+1)/len(df):.2%}"
        )

df["predicted_rssi"] = predictions

# ---------------------------------------
# Metrics
# ---------------------------------------

df["error"] = (
    df["predicted_rssi"]
    - df["rssi"]
)

df["abs_error"] = np.abs(
    df["error"]
)

print()
print("========== RESULTS ==========")

print(
    f"MAE : {df['abs_error'].mean():.3f}"
)

print(
    f"RMSE : {np.sqrt((df['error'] ** 2).mean()):.3f}"
)

print(
    f"Max error : {df['abs_error'].max():.3f}"
)

print(
    df.sort_values(
        "abs_error",
        ascending=False
    )[
        [
            "lat",
            "lon",
            "gateway",
            "rssi",
            "predicted_rssi",
            "error",
        ]
    ].head(5)
)

# ---------------------------------------
# Debug worst sample
# ---------------------------------------

print()
print("===================================")
print("DEBUG WORST SAMPLE")
print("===================================")

worst_idx = df["abs_error"].idxmax()

row = df.loc[
    worst_idx
]

# row = df.loc[10074]
print()
print("Original row :")
print(
    row[
        [
            "lat",
            "lon",
            "gateway",
            "frequency",
            "spreading_factor",
            "rssi"
        ]
    ]
)
