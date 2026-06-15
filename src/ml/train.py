import sys
import os

import pandas as pd
import numpy as np
import joblib

from sklearn.inspection import permutation_importance
from sklearn.model_selection import KFold, ParameterSampler, RandomizedSearchCV, cross_validate, train_test_split, cross_val_score
from sklearn.metrics import (
    root_mean_squared_error,
    mean_absolute_error,
    r2_score
)

# ── Configuration ──
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from config_loader import config  # noqa: E402

from ml import pipeline
from ml.pipeline import (
    build_pipeline,
    prepare_data
)

TRN = config["paths"]["training"]
KNN_CFG = config["knn"]

DATA_PATH = TRN["devices_history_csv"]

def train(
    model_type="extra_trees",

    MIN_DISTANCE=KNN_CFG["min_distance"],
    K=KNN_CFG["k"],
    K_SEARCH=KNN_CFG["k_search"],
    GW_DISTANCE_WEIGHT=KNN_CFG["gw_distance_weight"],

    show_importance=True,
    save_model=True
):

    print("Loading data...")
    df = pd.read_csv(DATA_PATH)

    kf = KFold(
        n_splits=5,
        shuffle=True,
        random_state=42
    )
    
    r2_scores = []
    mae_scores = []
    rmse_scores = []
    feature_importances = []
    pipeline = build_pipeline("extra_trees")

    for train_idx, test_idx in kf.split(df):

        train_df = df.iloc[train_idx].copy()
        test_df = df.iloc[test_idx].copy()

        X_train, y_train = prepare_data(
            train_df,
            reference_df=train_df,
            MIN_DISTANCE=MIN_DISTANCE,
            K=K,
            K_SEARCH=K_SEARCH,
            GW_DISTANCE_WEIGHT=GW_DISTANCE_WEIGHT
        )

        X_test, y_test = prepare_data(
            test_df,
            reference_df=train_df,
            MIN_DISTANCE=MIN_DISTANCE,
            K=K,
            K_SEARCH=K_SEARCH,
            GW_DISTANCE_WEIGHT=GW_DISTANCE_WEIGHT
        )

        pipeline.fit(X_train, y_train)

        pred = pipeline.predict(X_test)

        r2 = r2_score(
            y_test,
            pred
        )

        mae = mean_absolute_error(
            y_test,
            pred
        )

        rmse = root_mean_squared_error(
            y_test,
            pred
        )

        # importances = permutation_importance(
        #     pipeline,
        #     X_test,
        #     y_test,
        #     n_repeats=10,
        #     random_state=42,
        #     scoring="r2"
        # )

        # feature_importances.append(
        #     pd.Series(
        #         importances.importances_mean,
        #         index=X_test.columns
        #     )
        # )

        r2_scores.append(r2)
        mae_scores.append(mae)
        rmse_scores.append(rmse)


    print(
        f"R²   : "
        f"{np.mean(r2_scores):.4f}"
        f" ± "
        f"{np.std(r2_scores):.4f}"
        f"  MAE  : "
        f"{np.mean(mae_scores):.2f} dBm"
        f"  RMSE : "
        f"{np.mean(rmse_scores):.2f} dBm"
    )

    # if feature_importances:
    #     mean_importances = pd.concat(feature_importances, axis=1).mean(axis=1).sort_values(ascending=False)
    #     print("Feature importances:")
    #     for feature, importance in mean_importances.items():
    #         print(f"  {feature}: {importance:.6f}")

    # ------------------------
    # Final training on full dataset
    # ------------------------

    if save_model:

        print("Training final model on full data...")

        X, y = prepare_data(
            df,
            reference_df=df,
            MIN_DISTANCE=MIN_DISTANCE,
            K=K,
            K_SEARCH=K_SEARCH,
            GW_DISTANCE_WEIGHT=GW_DISTANCE_WEIGHT
        )

        final_pipeline = build_pipeline(model_type)
        final_pipeline.fit(X, y)

        # Generate a date-stamped filename from config template
        from datetime import date as _date
        date_str = _date.today().strftime("%Y%m%d")  # e.g. 20260615
        out_dir = TRN.get("model_output_dir", "ml/models")
        tmpl = TRN.get("model_filename_template", "{model_type}_model_{date}.pkl")
        model_filename = tmpl.replace("{model_type}", model_type).replace("{date}", date_str)
        model_path = os.path.join(out_dir, model_filename)

        print(f"Saving model to {model_path} ...")
        joblib.dump(
            final_pipeline,
            model_path,
            compress=("xz", 3)
        )
        print("Model saved.")

    print("Done.")
