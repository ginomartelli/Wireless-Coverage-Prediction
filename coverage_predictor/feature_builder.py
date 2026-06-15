import os
import sys

# ── Ensure sibling modules and project root are importable ──
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
import pandas as pd

from config_loader import config  # noqa: E402

from terrain import (
    get_elevation,
    get_slope,
    get_roughness,
    get_path_features,
)

from neighbor_features import (
    compute_neighbor_features,
    closest_reference_point,
    REFERENCE, LAT_TO_M, LON_TO_M, REFERENCE_TREE,
)

INF_CFG = config["paths"]["inference"]
RADIO = config["radio"]
KNN_CFG = config["knn"]
INFER = config["inference"]
ANT = config["antenna"]

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
GATEWAYS = pd.read_csv(os.path.join(BASE_DIR, INF_CFG["gateways_csv"]))


def haversine(lat1, lon1, lat2, lon2):

    R = 6371000

    phi1 = np.radians(lat1)
    phi2 = np.radians(lat2)

    dphi = np.radians(lat2 - lat1)
    dlambda = np.radians(lon2 - lon1)

    a = (
        np.sin(dphi / 2) ** 2
        +
        np.cos(phi1)
        * np.cos(phi2)
        * np.sin(dlambda / 2) ** 2
    )

    c = 2 * np.arcsin(
        np.sqrt(a)
    )

    return R * c

def build_features(
    lat,
    lon,
    gateway=None,
    frequency=RADIO["default_frequency"],
    spreading_factor=RADIO["default_spreading_factor"],
):

    ref, dist = closest_reference_point(lat, lon)

    # ── Out-of-Distribution (OOD) check ──
    # If the point is > 500km from any training data, it is OOD.
    if dist > 500_000:
        raise ValueError(f"Point ({lat}, {lon}) is Out-of-Distribution.")

    if dist <= INFER["closest_point_threshold_m"]:
        return ref["rssi"]
    # -------------------------
    # Gateway selection
    # -------------------------

    # -------------------------
    # Gateway selection & fallback
    # -------------------------
    _gateway_unknown = False

    if gateway is None:

        gateway = ref["gateway"]

        match = GATEWAYS[GATEWAYS["gateway"] == gateway]
        if len(match) == 0:
            # Fallback: use the first available gateway metadata
            _gateway_unknown = True
            match = GATEWAYS.iloc[:1]
            gw = match.iloc[0]
        else:
            gw = match.iloc[0]

    else:

        match = GATEWAYS[GATEWAYS["gateway"] == gateway]

        if len(match) == 0:
            # Unknown gateway — fallback: use the closest gateway's metadata
            _gateway_unknown = True
            closest_gw_id = ref["gateway"]
            match = GATEWAYS[GATEWAYS["gateway"] == closest_gw_id]
            if len(match) == 0:
                # Absolute fallback: pick first gateway
                match = GATEWAYS.iloc[:1]
            gw = match.iloc[0]

        elif len(match) == 1:

            gw = match.iloc[0]

        else:

            dist = (
                (match["gw_lat"] - lat) ** 2
                +
                (match["gw_lon"] - lon) ** 2
            )

            gw = match.loc[dist.idxmin()]

    gateway = gw["gateway"]

    gw_lat = gw["gw_lat"]
    gw_lon = gw["gw_lon"]
    gw_elevation = gw["gw_elevation"]

    gateway_distance = haversine(
        lat,
        lon,
        gw["gw_lat"],
        gw["gw_lon"]
    )

    if gateway_distance > gw["range"]:
        return INFER["out_of_range_rssi"]
    # -------------------------
    # Geometry
    # -------------------------

    distance = haversine(
        lat,
        lon,
        gw_lat,
        gw_lon,
    )

    delta_lat = (
        lat - gw_lat
    )

    delta_lon = (
        lon - gw_lon
    )

    angle = np.arctan2(
        delta_lat,
        delta_lon,
    )

    # -------------------------
    # Terrain
    # -------------------------

    elevation = get_elevation(
        lat,
        lon,
    )

    delta_elevation = (
        elevation
        -
        gw_elevation
        +
        ANT["device_height_m"]
        -
        ANT["gateway_height_m"]
    )

    distance_3d = np.sqrt(
        distance ** 2
        +
        delta_elevation ** 2
    )

    terrain = get_path_features(
        lat,
        lon,
        elevation,

        gw_lat,
        gw_lon,
        gw_elevation,

        distance,

        frequency,
    )

    # -------------------------
    # Neighbor features
    # -------------------------
    neighbor = (
        compute_neighbor_features(
            lat,
            lon,
            gateway,
            distance,
        )
    )

    # -------------------------
    # Final feature vector
    # -------------------------

    X = pd.DataFrame([{

        "frequency":
            frequency,

        "spreading_factor":
            spreading_factor,

        "distance_3d":
            distance_3d,

        "log_distance_3d":
            np.log10(
                distance_3d
            ),

        "rssi_closest_point":
            neighbor[
                "rssi_closest_point"
            ],

        "distance_closest_point":
            neighbor[
                "distance_closest_point"
            ],

        "closest_to_gw_distance":
            neighbor[
                "closest_to_gw_distance"
            ],

        "neighbor_rssi_mean":
            neighbor[
                "neighbor_rssi_mean"
            ],

        "neighbor_rssi_weighted_mean":
            neighbor[
                "neighbor_rssi_weighted_mean"
            ],

        "neighbor_rssi_std":
            neighbor[
                "neighbor_rssi_std"
            ],

        "neighbor_distance_mean":
            neighbor[
                "neighbor_distance_mean"
            ],

        "neighbor_gw_distance_mean":
            neighbor[
                "neighbor_gw_distance_mean"
            ],

        "delta_lat":
            delta_lat,

        "delta_lon":
            delta_lon,

        "angle":
            angle,

        "elevation":
            elevation,

        "gw_elevation":
            gw_elevation,

        "delta_elevation":
            delta_elevation,

        "elevation_angle":
            np.arctan2(
                delta_elevation,
                distance_3d,
            ),

        "slope":
            get_slope(
                lat,
                lon,
            ),

        "roughness":
            get_roughness(
                lat,
                lon,
            ),

        "terrain_mean":
            terrain[
                "terrain_mean"
            ],

        "terrain_std":
            terrain[
                "terrain_std"
            ],

        "terrain_min":
            terrain[
                "terrain_min"
            ],

        "terrain_max":
            terrain[
                "terrain_max"
            ],

        "terrain_range":
            terrain[
                "terrain_range"
            ],

        "max_obstruction":
            terrain[
                "max_obstruction"
            ],

        "fresnel_obstruction_ratio":
            terrain[
                "fresnel_obstruction_ratio"
            ],

        "min_fresnel_clearance":
            terrain[
                "min_fresnel_clearance"
            ],

        "mean_fresnel_clearance":
            terrain[
                "mean_fresnel_clearance"
            ],

        "residential_ratio":
            terrain[
                "residential_ratio"
            ],

        "gateway":
            gateway,

        "gateway_unknown":
            1.0 if _gateway_unknown else 0.0,

    }])

    return X