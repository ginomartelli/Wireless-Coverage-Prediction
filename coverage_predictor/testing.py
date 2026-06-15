import numpy as np
import pandas as pd

import predictor

df_ref = pd.read_csv("./data/reference_points.csv")
df_test = pd.read_csv("./data/devices_history_full.csv")

df_pred = pd.read_csv("./data/predicted_test_points.csv")
mean_absolute_error = np.mean(abs(df_pred["rssi_true"] - df_pred["rssi_pred"]))
root_mean_squared_error = np.sqrt(np.mean((df_pred["rssi_true"] - df_pred["rssi_pred"]) ** 2))

print(f"Mean Absolute Error: {mean_absolute_error:.2f}")
print(f"Root Mean Squared Error: {root_mean_squared_error:.2f}")

cols = ["lat", "lon", "rssi"]

df_test = (
    df_test
    .merge(df_ref[cols], on=cols, how="left", indicator=True)
    .query("_merge == 'left_only'")
    .drop(columns="_merge")
)

df_test.to_csv("./data/test_points.csv", index=False)

mae = []
rmse = []
df_pred = []
for idx, row in df_test.iterrows():
    lat = row["lat"]
    lon = row["lon"]
    gateway = row["gateway"]
    frequency = row["frequency"]
    spreading_factor = row["spreading_factor"]
    rssi_true = row["rssi"]
    rssi_pred = predictor.predict(lat, lon, gateway=gateway, frequency=frequency, spreading_factor=spreading_factor)
    mae.append(abs(rssi_true - rssi_pred))
    rmse.append((rssi_true - rssi_pred) ** 2)
    df_pred.append({
        "lat": lat,
        "lon": lon,
        "gateway": gateway,
        "frequency": frequency,
        "spreading_factor": spreading_factor,
        "rssi_true": rssi_true,
        "rssi_pred": rssi_pred
    })
    print(f"Test point {idx+1}/{len(df_test)}: True RSSI={rssi_true}, Predicted RSSI={rssi_pred:.2f}")

print(f"Mean Absolute Error: {np.mean(mae):.2f}")
print(f"Root Mean Squared Error: {np.sqrt(np.mean(rmse)):.2f}")

df_pred = pd.DataFrame(df_pred)
df_pred.to_csv("./data/predicted_test_points.csv", index=False)