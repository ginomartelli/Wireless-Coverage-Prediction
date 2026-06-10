import numpy as np
from scipy.spatial import cKDTree

def haversine(lat1, lon1, lat2, lon2): #maybe change for caclulating 3D distance with elevation bc pythagore=/=arcs so approximation
    R = 6371000  # mètres

    phi1 = np.radians(lat1)
    phi2 = np.radians(lat2)
    dphi = np.radians(lat2 - lat1)
    dlambda = np.radians(lon2 - lon1)

    a = np.sin(dphi/2)**2 + np.cos(phi1)*np.cos(phi2)*np.sin(dlambda/2)**2
    c = 2 * np.arcsin(np.sqrt(a))

    return R * c

def add_basic_features(df):
    df["distance"] = haversine(
        df["lat"], df["lon"],
        df["gw_lat"], df["gw_lon"]
    )

    df["log_distance"] = np.log10(df["distance"])

    df = add_geometry_features(df)

    df["gateway_id"] = df["gateway"].astype("category").cat.codes

    # df = add_closest_point_features(df) // not here for train-test split

    return df

def add_geometry_features(df):
    df["delta_lat"] = df["lat"] - df["gw_lat"]
    df["delta_lon"] = df["lon"] - df["gw_lon"]
    df["angle"] = np.arctan2(
        df["delta_lat"],
        df["delta_lon"]
    )
    return df

def add_closest_point_features(
    df,
    reference_df=None,
    MIN_DISTANCE=0.1,
    K=9,
    K_SEARCH=11,
    GW_DISTANCE_WEIGHT=1.1
):

    if reference_df is None:
        reference_df = df

    same_df = (reference_df is df)

    LAT_TO_M = 111000.0
    LON_TO_M = (
        111000.0 *
        np.cos(
            np.radians(
                reference_df["lat"].mean()
            )
        )
    )

    gateway_data = {}

    # ---------------------------------------
    # Préparation par gateway
    # ---------------------------------------

    for gw in reference_df["gateway"].unique():

        mask = (
            reference_df["gateway"] == gw
        )

        ref = reference_df.loc[mask]

        coords = np.column_stack([
            ref["lat"].values * LAT_TO_M,
            ref["lon"].values * LON_TO_M
        ])

        gateway_data[gw] = {
            "tree": cKDTree(coords),
            "coords": coords,
            "rssi": ref["rssi"].values,
            "gw_dist": ref["distance"].values,
            "lat": ref["lat"].values,
            "lon": ref["lon"].values,
        }

    # ---------------------------------------

    rssi_closest_super_point = []
    rssi_closest_point = []

    distance_closest_point = []

    closest_to_gw_distance = []
    ratio_gateway_distance = []

    neighbor_rssi_mean = []
    neighbor_rssi_weighted_mean = []
    neighbor_rssi_std = []

    neighbor_distance_mean = []

    neighbor_gw_distance_mean = []
    neighbor_ratio_gateway_distance = []

    # ---------------------------------------

    for _, row in df.iterrows():

        gw = row["gateway"]

        data = gateway_data[gw]

        tree = data["tree"]

        point = np.array([
            row["lat"] * LAT_TO_M,
            row["lon"] * LON_TO_M
        ])

        my_gw_dist = row["distance"]

        # ----------------------------
        # Super point
        # ----------------------------

        local_idx = tree.query_ball_point(
            point,
            r=MIN_DISTANCE
        )

        if same_df:

            local_idx = [
                i for i in local_idx
                if not (
                    data["lat"][i] == row["lat"]
                    and
                    data["lon"][i] == row["lon"]
                )
            ]

        if len(local_idx):

            local_dist = np.linalg.norm(
                data["coords"][local_idx]
                -
                point,
                axis=1
            )

            w = np.exp(
                -local_dist / 2.0
            )

            rssi_closest_super_point.append(
                np.sum(
                    data["rssi"][local_idx] * w
                )
                /
                np.sum(w)
            )

        else:

            rssi_closest_super_point.append(
                np.nan
            )

        # ----------------------------
        # Recherche candidats
        # ----------------------------

        dist_all, idx_all = tree.query(
            point,
            k=min(
                K_SEARCH,
                len(data["rssi"])
            )
        )

        dist_all = np.atleast_1d(
            dist_all
        )

        idx_all = np.atleast_1d(
            idx_all
        )

        keep = []

        for d, idx in zip(
            dist_all,
            idx_all
        ):

            if d <= MIN_DISTANCE:
                continue

            keep.append(
                (d, idx)
            )

        if len(keep) == 0:

            rssi_closest_point.append(
                np.nan
            )

            distance_closest_point.append(
                np.nan
            )

            closest_to_gw_distance.append(
                np.nan
            )

            ratio_gateway_distance.append(
                np.nan
            )

            neighbor_rssi_mean.append(
                np.nan
            )

            neighbor_rssi_weighted_mean.append(
                np.nan
            )

            neighbor_rssi_std.append(
                np.nan
            )

            neighbor_distance_mean.append(
                np.nan
            )

            neighbor_gw_distance_mean.append(
                np.nan
            )

            neighbor_ratio_gateway_distance.append(
                np.nan
            )

            continue

        dist_keep = np.array([
            x[0]
            for x in keep
        ])

        idx_keep = np.array([
            x[1]
            for x in keep
        ])

        score = (
            dist_keep
            +
            GW_DISTANCE_WEIGHT
            *
            np.abs(
                data["gw_dist"][
                    idx_keep
                ]
                -
                my_gw_dist
            )
        )

        order = np.argsort(
            score
        )[:K]

        idx = idx_keep[
            order
        ]

        dist = dist_keep[
            order
        ]

        rssi = data["rssi"][
            idx
        ]

        gw_dist = data["gw_dist"][
            idx
        ]

        # Closest

        rssi_closest_point.append(
            rssi[0]
        )

        distance_closest_point.append(
            dist[0]
        )

        closest_to_gw_distance.append(
            gw_dist[0]
        )

        ratio_gateway_distance.append(
            gw_dist[0]
            /
            (
                my_gw_dist
                + 1e-6
            )
        )

        # KNN

        neighbor_rssi_mean.append(
            np.mean(rssi)
        )

        neighbor_rssi_std.append(
            np.std(rssi)
        )

        w = np.exp(
            -dist / 30
        )

        neighbor_rssi_weighted_mean.append(
            np.sum(
                rssi * w
            )
            /
            np.sum(w)
        )

        neighbor_distance_mean.append(
            np.mean(dist)
        )

        neighbor_gw_distance_mean.append(
            np.mean(gw_dist)
        )

        neighbor_ratio_gateway_distance.append(
            np.mean(
                gw_dist
                /
                (
                    my_gw_dist
                    + 1e-6
                )
            )
        )

    df["rssi_closest_super_point"] = rssi_closest_super_point

    df["rssi_closest_point"] = rssi_closest_point
    df["distance_closest_point"] = distance_closest_point

    df["closest_to_gw_distance"] = closest_to_gw_distance
    df["ratio_gateway_distance"] = ratio_gateway_distance

    df["neighbor_rssi_mean"] = neighbor_rssi_mean
    df["neighbor_rssi_weighted_mean"] = neighbor_rssi_weighted_mean
    df["neighbor_rssi_std"] = neighbor_rssi_std

    df["neighbor_distance_mean"] = neighbor_distance_mean

    df["neighbor_gw_distance_mean"] = neighbor_gw_distance_mean
    df["neighbor_ratio_gateway_distance"] = neighbor_ratio_gateway_distance


    return df