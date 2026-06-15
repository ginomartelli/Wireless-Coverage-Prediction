bounds=(108.08, 15.87, 108.32, 16.12) pour la carte dl sur "OpenTopography : changed to  Xmin = 107.0804443527013	  Ymin = 15.15856441049533	  Xmax = 108.97888205386698	  Ymax = 16.70512780665861

https://docs.google.com/spreadsheets/d/1hss_oUUUP1r3d4MA8pTS3w_L92m9-wUM-oP_nc6zV4I/edit?pli=1&gid=1161341563#gid=1161341563 

High-Resolution Topography Data and Tools"
Dataset Citation: NASA Shuttle Radar Topography Mission (SRTM)(2013). Shuttle Radar Topography Mission (SRTM) Global. Distributed by OpenTopography. https://doi.org/10.5069/G9445JDF. Accessed 2026-05-07       
Use License: Not Provided

bounds2=(106.05, 20.65,106.65, 20.92 )

Gateway 7276ff002e062cf2 at longitude 108.273681640625 and latitude 16.118301391601562 : delta elevation crazy -> verif gg maps : Son tra sommet montagne.

===== RESULTS ===== RANDOM FOREST
MAE  : 2.15 dBm
RMSE : 3.77 dBm
R²   : 0.8872
features importance avec random forest : 
                          feature    importance
17                num__terrain_max  2.637750e-01
12                      num__slope  1.877622e-01
9             num__delta_elevation  6.890332e-02
16                num__terrain_min  6.505000e-02
10            num__elevation_angle  6.306178e-02
30   cat__gateway_7076ff0054070418  4.933417e-02
29   cat__gateway_24e124fffef4778e  4.492214e-02
33   cat__gateway_7276ff002e061f5b  2.529312e-02Local\src> 
0                   num__frequency  2.492653e-02
6             num__log_distance_3d  2.051328e-02
24     num__mean_fresnel_clearance  1.960808e-02
4                num__log_distance  1.846207e-02
3                    num__distance  1.818727e-02
5                 num__distance_3d  1.789327e-02
11                       num__fspl  1.772674e-02
8                num__gw_elevation  1.274121e-02
14               num__terrain_mean  1.007954e-02
15                num__terrain_std  9.766615e-03
23      num__min_fresnel_clearance  8.763362e-03
13                  num__roughness  8.557575e-03
39   cat__gateway_ac1f09fffe06fcf2  6.550217e-03
7                   num__elevation  5.592362e-03
22  num__fresnel_obstruction_ratio  4.843328e-03
2            num__spreading_factor  4.351444e-03
28              num__unknown_ratio  3.906185e-03
26                num__water_ratio  2.941676e-03
35   cat__gateway_a840411eebb44150  2.536600e-03
27          num__residential_ratio  2.507375e-03
20            num__max_obstruction  2.203351e-03
32   cat__gateway_7276ff002e06029f  1.562875e-03
18              num__terrain_range  1.447215e-03
19          num__obstruction_ratio  1.085998e-03
21           num__mean_obstruction  9.805402e-04
40   cat__gateway_ac1f09fffe0fd629  9.325536e-04
44    cat__terrain_type_industrial  9.258665e-04
48       cat__terrain_type_unknown  7.576351e-04
45   cat__terrain_type_residential  6.207596e-04
31   cat__gateway_7276ff002e0507da  2.479060e-04
37   cat__gateway_ac1f09fffe00ab20  1.946673e-04
38   cat__gateway_ac1f09fffe00ab25  1.514256e-04
36   cat__gateway_a84041ffff1ec39f  1.265952e-04
49         cat__terrain_type_water  9.773065e-05
25               num__forest_ratio  4.098980e-05
47         cat__terrain_type_scrub  3.337776e-05
43         cat__terrain_type_grass  1.809893e-05
42        cat__terrain_type_forest  6.747524e-06
41   cat__gateway_ac1f09fffe0fd63b  6.417541e-06
46        cat__terrain_type_retail  1.091230e-06
34   cat__gateway_7276ff002e062cf2  9.835633e-07
50          cat__terrain_type_wood  7.153526e-07
1                   num__bandwidth  0.000000e+00

FEATURE IMPORTANCE AVEC PERMUTATION : 
                      feature  importance
17                terrain_max    0.855852
12                      slope    0.594322
29                    gateway    0.388132
10            elevation_angle    0.129914
0                   frequency    0.118720
9             delta_elevation    0.094341
8                gw_elevation    0.082720
16                terrain_min    0.063295
2            spreading_factor    0.031659
24     mean_fresnel_clearance    0.029499
14               terrain_mean    0.009252
13                  roughness    0.009103
23      min_fresnel_clearance    0.006886
6             log_distance_3d    0.006814
22  fresnel_obstruction_ratio    0.005851
4                log_distance    0.005586
5                 distance_3d    0.005220
11                       fspl    0.005077
7                   elevation    0.004877
3                    distance    0.004797
15                terrain_std    0.004556
27          residential_ratio    0.003428
28              unknown_ratio    0.003374
20            max_obstruction    0.001277
__________________________________________
26                water_ratio    0.000674
30               terrain_type    0.000197
19          obstruction_ratio    0.000048
1                   bandwidth    0.000000
25               forest_ratio   -0.000022
21           mean_obstruction   -0.000032
18              terrain_range   -0.000308

FEATURES enlevé : celles inf a  max obstruction
went from : RESULTS : RANDOM_FOREST
MAE  : 2.15 dBm
RMSE : 3.77 dBm
R²   : 0.8872
TO : RESULTS : RANDOM_FOREST
MAE  : 2.14 dBm
RMSE : 3.77 dBm
R²   : 0.8875
AND FROM : RESULTS : XGBOOST
MAE  : 2.33 dBm
RMSE : 4.20 dBm
R²   : 0.8602
TO : RESULTS : XGBOOST
MAE  : 2.36 dBm
RMSE : 4.24 dBm
R²   : 0.8577

Features maj :
added
    "delta_lat", 
    "delta_lon",
    "angle",
removed 
    # "distance",
    # "distance_3d",
    # "unknown_ratio",
    # "fspl"
    # "elevation",
   
TO RESULTS : RANDOM_FOREST
MAE : 2.12 dBm
RMSE : 3.77 dBm
R² : 0.8872
AVEC : 
                      feature  importance
15                terrain_max    0.800356
10                      slope    0.398399
20                    gateway    0.385218
0                   frequency    0.119552
8             delta_elevation    0.089288
7                gw_elevation    0.082437
9             elevation_angle    0.070411
14                terrain_min    0.065715
6                       angle    0.043304
18     mean_fresnel_clearance    0.034972
1            spreading_factor    0.031614
3             log_distance_3d    0.031401
4                   delta_lat    0.021302
2                log_distance    0.018730
12               terrain_mean    0.008000
19          residential_ratio    0.007417
11                  roughness    0.006889
17      min_fresnel_clearance    0.005978
16  fresnel_obstruction_ratio    0.003996
13                terrain_std    0.002767
5                   delta_lon    0.001093

Features finalisé.
choix du model, hyperparametres et k fold:
RESULTS : RANDOM_FOREST
MAE  : 2.11 dBm
RMSE : 3.42 dBm
R²   : 0.9073
{'model__n_estimators': 500, 'model__min_samples_split': 2, 'model__min_samples_leaf': 1, 'model__max_features': 'sqrt', 'model__max_depth': 20}
Best CV score: 0.8928582828174534

RESULTS : EXTRA_TREES
MAE  : 2.03 dBm
RMSE : 3.45 dBm
R²   : 0.9056
{'model__n_estimators': 1500, 'model__min_samples_split': 5, 'model__min_samples_leaf': 2, 'model__max_features': None, 'model__max_depth': 20}
Best CV score: 0.9043157603128187

RESULTS : XGBOOST : NUL
MAE  : 2.14 dBm
RMSE : 3.80 dBm
R²   : 0.8857
{'model__subsample': 0.8, 'model__n_estimators': 1000, 'model__max_depth': 10, 'model__learning_rate': 0.01, 'model__colsample_bytree': 1.0}
Best CV score:
0.8962056994438171

RESULTS : HIST_GRAD_BOOST : NUL
MAE  : 2.22 dBm
RMSE : 3.72 dBm
R²   : 0.8904
{'model__min_samples_leaf': 20, 'model__max_leaf_nodes': 31, 'model__max_depth': None, 'model__learning_rate': 0.1, 'model__l2_regularization': 0.0}
Best CV score:
0.8851964577354531

RESULTS : MLP_REG : NUL
MAE  : 2.58 dBm
RMSE : 4.19 dBm
R²   : 0.8609
{'model__hidden_layer_sizes': (100,), 'model__alpha': 0.01, 'model__activation': 'tanh'}
Best CV score:
0.8477885945374343

RESULTS : SVR : NUL
MAE  : 2.79 dBm
RMSE : 5.49 dBm
R²   : 0.7610
{'model__kernel': 'rbf', 'model__epsilon': 0.5, 'model__C': 10.0}
Best CV score:
0.7406420868442494

Les principales familles d'algorithmes de régression supervisée ont été évaluées : 
Bagging → RF, ExtraTrees
Boosting → XGBoost, HistGradientBoost
Réseau de neurones → MLP
Méthode à noyau → SVR

Les deux meilleurs modèles sont :
Random Forest
Extra Trees

comparaison : 
SUR SPATIAL SPLIT :
RESULTS : RANDOM_FOREST
MAE  : 21.98 dBm
RMSE : 25.50 dBm
R²   : -0.3532

RESULTS : EXTRA_TREES
MAE  : 24.26 dBm
RMSE : 27.51 dBm
R²   : -0.5754

SUR 5 fold shuffled : 
RESULTS : RANDOM_FOREST
R²   : 0.9065496122245399
MAE  : 2.0723521650301495
RMSE : 3.3343703140599117

RESULTS : EXTRA_TREES : MODEL FINAL
R²   : 0.9106026878497498
MAE  : 2.003640836176458
RMSE : 3.2613100891320825

Random Forest and Extra Trees achieved very similar performances. Extra Trees obtained the best average cross-validation scores (R²=0.911, MAE=2.00 dBm, RMSE=3.26 dBm) and was therefore selected as the final model.


Concernant le std :
Si tu observes :
RF = légèrement plus stable
ET = légèrement plus précis
alors :
Si ton objectif est la meilleure prédiction
→ prends Extra Trees
Si ton objectif est la robustesse / reproductibilité
→ prends Random Forest

NOUVELLE FEATURES : 
"rssi_closest_point",
"distance_closest_point",
"closest_to_gw_distance",
"ratio_gateway_distance", 
removed distance et log distance car distance 3D et log distance 3D


Two versions of the nearest-neighbor feature were investigated. During model evaluation, a minimum separation distance was imposed to prevent the model from relying exclusively on nearly identical neighboring samples. For the final deployment model, this constraint was removed to maximize prediction accuracy using all available historical measurements.
SUR cross val avec limite du closest point a 150  metres : 
RESULTS : RANDOM_FOREST
R²   : 0.9117 ± 0.0070
MAE  : 2.05 dBm
RMSE : 3.24 dBm

RESULTS : EXTRA_TREES MODEL : 
              feature  importance       std
4          rssi_closest_point    0.239885  0.048665
24                    gateway    0.190168  0.023612
3             log_distance_3d    0.111555  0.008721
0                   frequency    0.111023  0.034419
13            elevation_angle    0.098243  0.008156
23          residential_ratio    0.080263  0.055661
5      distance_closest_point    0.061426  0.016352
1            spreading_factor    0.033361  0.004764
14                      slope    0.026361  0.003941
19                terrain_max    0.022847  0.001826
10                      angle    0.021595  0.005546
11               gw_elevation    0.020642  0.006190
16               terrain_mean    0.019860  0.004654
15                  roughness    0.017830  0.007863
2                 distance_3d    0.012183  0.002222
18                terrain_min    0.012053  0.002477
8                   delta_lat    0.006114  0.001073
9                   delta_lon    0.004717  0.001679
7      ratio_gateway_distance    0.003759  0.000906
6      closest_to_gw_distance    0.003616  0.001541
21      min_fresnel_clearance    0.002633  0.001129
17                terrain_std    0.002242  0.001254
22     mean_fresnel_clearance    0.002044  0.001170
12            delta_elevation    0.001624  0.000792
20  fresnel_obstruction_ratio    0.001414  0.000732

Cross validation results for model: extra_trees
R²   : 0.9135 ± 0.0066
MAE  : 2.00 dBm
RMSE : 3.21 dBm

look for data issues/outliers by looking at the 10 worst pred : 
10 pires prédictions du modèle 2:
       device        lat         lon           gateway  ...  ratio_gateway_distance  is_closest_toward_gateway  predicted_rssi_2  error_model_2
6009    node3  16.092370  108.141370  ac1f09fffe00ab25  ...                1.000000                          0       -121.981420      31.981420
6043    node3  16.092370  108.141370  ac1f09fffe00ab25  ...                1.000000                          0       -123.865086      28.865086
9983   node01  20.918076  106.638658  24e124fffef4778e  ...                1.000000                          0        -96.200360      17.799640
6044    node3  16.092370  108.141370  ac1f09fffe00ab25  ...                1.000000                          0       -121.981420      14.981420
9368   node01  20.894838  106.592253  24e124fffef4778e  ...              622.382798                          0        -76.606770      14.606770
ISSUE : exact same location with differents rssi.
ratio gateway of 622 /!\ ? normal ou pas ?
distance <150 but we forced distance > 150 ?

same loc : 
                                       count        std
lat       lon        gateway                           
20.917733 106.638723 24e124fffef4778e     29  17.155619
20.654578 106.063381 24e124fffef4778e      2  11.313708
20.654440 106.063366 7076ff0054070418      2   9.192388
20.918076 106.638658 24e124fffef4778e     11   8.956460
16.092370 108.141370 ac1f09fffe00ab25     39   8.738748
20.918148 106.638671 24e124fffef4778e      2   7.778175
20.917868 106.638756 7076ff0054070418      2   7.778175
16.016105 108.213621 7276ff002e061f5b      2   6.363961
20.654346 106.063301 24e124fffef4778e      2   6.363961
20.654448 106.063405 7076ff0054070418     24   5.562393
20.917056 106.636840 24e124fffef4778e      3   5.196152
16.060720 108.162170 ac1f09fffe0fd629     49   4.995151
16.073140 108.149880 ac1f09fffe0fd629     44   4.622081
20.654436 106.063300 24e124fffef4778e      3   4.618802
16.081030 108.223850 ac1f09fffe00ab25      4   4.272002
20.654503 106.063433 24e124fffef4778e      2   4.242641
20.654395 106.062725 24e124fffef4778e      4   4.123106
16.016105 108.213621 7276ff002e062cf2     13   3.733081
16.023836 108.206170 7276ff002e062cf2     11   3.590391
16.073941 108.152558 ac1f09fffe0fd629      2   3.535534

Multiple measurements acquired at identical locations were intentionally preserved. Preliminary experiments using median aggregation over duplicated coordinates resulted in a significant degradation of predictive performance (R² decreasing from 0.913 to 0.836), suggesting that repeated observations capture part of the natural variability of the radio channel rather than simple measurement noise.
Multiple measurements collected at identical geographical locations were intentionally preserved. Although these repeated observations introduce local variability, they represent the intrinsic stochastic behavior of LoRa radio propagation and significantly improve local interpolation performance.
EN EFFET, AFTER AGREG et TRAIN : avec         #CLEANING DUPLICATES
        agg_dict = {col: "first" for col in df.columns}
        agg_dict["rssi"] = "median"
        for col in ["lat", "lon", "gateway"]:
            agg_dict.pop(col, None)
        df = (
            df.groupby(["lat", "lon", "gateway"], as_index=False)
            .agg(agg_dict)
        )

        on a :
                      feature  importance       std
4          rssi_closest_point    0.686802  0.250295
24                    gateway    0.324027  0.061532
1            spreading_factor    0.106701  0.018501
13            elevation_angle    0.103856  0.012294
3             log_distance_3d    0.098158  0.009037
23          residential_ratio    0.032145  0.022049
10                      angle    0.027983  0.007617
2                 distance_3d    0.019844  0.002753
11               gw_elevation    0.013106  0.006283
14                      slope    0.011158  0.003029
19                terrain_max    0.008367  0.005487
18                terrain_min    0.008332  0.003830
16               terrain_mean    0.008177  0.006378
5      distance_closest_point    0.007097  0.002872
0                   frequency    0.007013  0.001446
7      ratio_gateway_distance    0.005906  0.001292
8                   delta_lat    0.005895  0.002525
22     mean_fresnel_clearance    0.005638  0.003310
9                   delta_lon    0.005478  0.003253
21      min_fresnel_clearance    0.005288  0.002470
20  fresnel_obstruction_ratio    0.003747  0.002481
15                  roughness    0.003328  0.002645
12            delta_elevation    0.003045  0.002300
6      closest_to_gw_distance    0.002803  0.001354
17                terrain_std    0.002367  0.003384

Cross validation results for model: extra_trees
R²   : 0.8363 ± 0.0096
MAE  : 2.27 dBm
RMSE : 3.49 dBm
NULL DONC MODEL SANS AGREG (pas de pb avec les 150 m enft).


donc :
The minimum distance used for the nearest-neighbor-derived features was treated as a hyperparameter and optimized experimentally. A threshold of *FIND IT* m provided the best cross-validation performance by reducing the influence of highly noisy repeated measurements collected at identical locations.
model 0 m :
R²   : 0.8937 ± 0.0130
MAE  : 2.24 dBm
RMSE : 3.55 dBm
model 1m :
R²   : 0.9142 ± 0.0104
MAE  : 2.03 dBm
RMSE : 3.19 dBm
model 5 m :
R²   : 0.9163 ± 0.0083
MAE  : 2.02 dBm
RMSE : 3.16 dBm
model 30 m:
R²   : 0.9116 ± 0.0067
MAE  : 2.05 dBm
RMSE : 3.25 dBm
model 50 m:
R²   : 0.9088 ± 0.0105
MAE  : 2.06 dBm
RMSE : 3.29 dBm
model 75m:
R²   : 0.9114 ± 0.0098
MAE  : 2.05 dBm
RMSE : 3.24 dBm
model 100m:
R²   : 0.9107 ± 0.0072
MAE  : 2.05 dBm
RMSE : 3.26 dBm
model 125:
R²   : 0.9134 ± 0.0071
MAE  : 2.04 dBm
RMSE : 3.21 dBm
model 150m :
RMSE : 3.29 dBm
R²   : 0.9135 ± 0.0066
MAE  : 2.00 dBm
RMSE : 3.21 dBm
model 200 : 
R²   : 0.9113 ± 0.0085
MAE  : 2.05 dBm
RMSE : 3.25 dBm
model 300:
R²   : 0.9110 ± 0.0077
MAE  : 2.06 dBm
RMSE : 3.26 dBm

ajout des features suivante (non commentées) : 
    # "rssi_closest_point",
    # "distance_closest_point",
    # "log_distance_closest_point", #already in distance closest point
    # "closest_to_gw_distance",
    # "ratio_gateway_distance",
    # "is_closest_toward_gateway", #low importance
    
    "neighbor_rssi_mean",
    # "neighbor_rssi_median",
    "neighbor_rssi_std",
    # "neighbor_rssi_min",
    # "neighbor_rssi_max",
    "neighbor_distance_mean",
    # "neighbor_distance_min",
    # "neighbor_distance_max",
    "neighbor_gw_distance_mean",
    "neighbor_ratio_gateway_distance",
    "neighbor_count",


result avec MIN DIST 5, K 5 : 
                            feature    importance           std
4                neighbor_rssi_mean  6.204168e-01  7.296570e-02
26                          gateway  1.461582e-01  2.450535e-02
0                         frequency  9.041329e-02  3.807950e-02
1                  spreading_factor  2.665518e-02  2.727740e-03
25                residential_ratio  2.590400e-02  6.364856e-03
3                   log_distance_3d  1.923461e-02  1.884177e-03
15                  elevation_angle  1.819310e-02  3.205745e-03
7         neighbor_gw_distance_mean  1.514864e-02  4.859222e-03
13                     gw_elevation  1.010406e-02  2.063227e-03
18                     terrain_mean  7.256966e-03  1.992914e-03
5                 neighbor_rssi_std  6.856551e-03  6.866114e-03
21                      terrain_max  6.624088e-03  1.497757e-03
16                            slope  6.192092e-03  1.253571e-03
6            neighbor_distance_mean  5.187384e-03  1.784439e-03
12                            angle  4.160558e-03  1.396071e-03
17                        roughness  3.998869e-03  1.423894e-03
20                      terrain_min  2.441563e-03  3.344028e-04
8   neighbor_ratio_gateway_distance  2.343578e-03  1.084752e-03
2                       distance_3d  2.156755e-03  1.456560e-03
10                        delta_lat  1.200826e-03  6.511295e-04
19                      terrain_std  9.125121e-04  4.714885e-04
11                        delta_lon  8.983316e-04  4.294538e-04
22        fresnel_obstruction_ratio  3.919073e-04  5.680755e-04
23            min_fresnel_clearance  3.587955e-04  7.361682e-04
24           mean_fresnel_clearance  2.710921e-04  4.956569e-04
14                  delta_elevation  1.259835e-04  1.587484e-04
9                    neighbor_count  1.554312e-17  3.688882e-17

Cross validation results for model: extra_trees
R²   : 0.9142 ± 0.0086
MAE  : 2.00 dBm
RMSE : 3.20 dBm

nouveau test avec features neighbor :
changement : 
    "rssi_closest_point",
    "distance_closest_point",
    # "closest_to_gw_distance",
    # "ratio_gateway_distance",
    "neighbor_rssi_mean",
    # "neighbor_rssi_median",
    "neighbor_rssi_std",
    "neighbor_distance_mean",
    "neighbor_gw_distance_mean",
    "neighbor_ratio_gateway_distance",
    "neighbor_rssi_weighted_mean",
    on a :
                            feature  importance       std
11      neighbor_rssi_weighted_mean    0.153744  0.026260
6                neighbor_rssi_mean    0.144156  0.018755
28                          gateway    0.122505  0.032396
0                         frequency    0.080772  0.040602
4                rssi_closest_point    0.062157  0.013402
1                  spreading_factor    0.025118  0.002677
27                residential_ratio    0.016980  0.007664
17                  elevation_angle    0.006970  0.000772
9         neighbor_gw_distance_mean    0.005503  0.004246
3                   log_distance_3d    0.005275  0.001276
23                      terrain_max    0.003704  0.000778
15                     gw_elevation    0.003641  0.000940
8            neighbor_distance_mean    0.002983  0.000817
7                 neighbor_rssi_std    0.002976  0.003477
18                            slope    0.002909  0.000890
20                     terrain_mean    0.002807  0.000908
5            distance_closest_point    0.002433  0.000764
14                            angle    0.001981  0.000670
10  neighbor_ratio_gateway_distance    0.001598  0.000332
19                        roughness    0.001300  0.000599
2                       distance_3d    0.001259  0.001113
21                      terrain_std    0.000978  0.000285
13                        delta_lon    0.000864  0.000495
12                        delta_lat    0.000758  0.000805
24        fresnel_obstruction_ratio    0.000534  0.000782
22                      terrain_min    0.000520  0.000265
25            min_fresnel_clearance    0.000400  0.000603
16                  delta_elevation    0.000180  0.000079
26           mean_fresnel_clearance    0.000146  0.000426

Cross validation results for model: extra_trees
R²   : 0.9150 ± 0.0096
MAE  : 2.00 dBm
RMSE : 3.18 dBm

changement : removed fresnels features, terrain_min, deltas lat/lon/elevation. ajout de :
    "closest_to_gw_distance",
    "ratio_gateway_distance",
    "path_rssi_mean",
    "path_rssi_weighted_mean",
    "path_rssi_std",
    "path_distance_mean",
result : 
    R²   : 0.9040 ± 0.0080
    MAE  : 2.12 dBm
    RMSE : 3.39 dBm

trop de features correlées avec certaines pas forcement meilleur donc on repart du meilleur model R²   : 0.9163 ± 0.0083 et on ajoute feature par feature avec seulement neighbors car path tres similaire.
AVEC 5CV pour R² mais importance sur fit X,y : 
                        feature  importance       std
31                      gateway    0.208434  0.004446
0                     frequency    0.155086  0.010064
30            residential_ratio    0.145462  0.001642
8   neighbor_rssi_weighted_mean    0.099629  0.001239
7            neighbor_rssi_mean    0.070165  0.000602
15                    elevation    0.062391  0.001195
18              elevation_angle    0.046241  0.001076
1              spreading_factor    0.045335  0.000652
4            rssi_closest_point    0.040528  0.000660
3               log_distance_3d    0.039977  0.000449
20                    roughness    0.037744  0.000264
21                 terrain_mean    0.030532  0.000183
16                 gw_elevation    0.028370  0.000449
19                        slope    0.023335  0.000974
24                  terrain_max    0.018830  0.000390
14                        angle    0.010928  0.000245
6        closest_to_gw_distance    0.008957  0.000370
2                   distance_3d    0.008738  0.000106
13                    delta_lon    0.007519  0.000385
23                  terrain_min    0.007497  0.000206
11    neighbor_gw_distance_mean    0.007311  0.000259
12                    delta_lat    0.005141  0.000113
29       mean_fresnel_clearance    0.004555  0.000130
22                  terrain_std    0.004185  0.000113
26              max_obstruction    0.003960  0.000172
9             neighbor_rssi_std    0.003955  0.000099
17              delta_elevation    0.003582  0.000049
27    fresnel_obstruction_ratio    0.002995  0.000080
28        min_fresnel_clearance    0.002851  0.000050
5        distance_closest_point    0.002793  0.000090
25                terrain_range    0.002734  0.000051
10       neighbor_distance_mean    0.002471  0.000043

Cross validation results for model: extra_trees
R²   : 0.9168 ± 0.0082
MAE  : 2.00 dBm
RMSE : 3.15 dBm

hyperparametres features closest points DISTANCE MIN, K:
MIN_DISTANCE=0.1, K=9, K_SEARCH=11, GW_DISTANCE_WEIGHT=1.1:
R²   : 0.9214 ± 0.0068  MAE  : 1.96 dBm  RMSE : 3.06 dBm
hyperparametres ml : 
0.92567 {'model__n_estimators': 650, 'model__min_samples_split': 10, 'model__max_features': 0.7, 'model__max_depth': 18}
0.92569 {'model__n_estimators': 1500, 'model__min_samples_split': 10, 'model__max_features': 0.7, 'model__max_depth': 18}
Donc prendre 650 car model plus rapide et leger 

stats model final :
R²   : 0.9257 ± 0.0066  MAE  : 1.95 dBm  RMSE : 2.98 dBm
10 worst predictions:
            lat         lon  gateway_id     distance  rssi  predicted_rssi      error
6009  16.092370  108.141370           9  2457.200022   -90     -121.635713  31.635713
6043  16.092370  108.141370           9  2457.200022   -95     -124.273468  29.273468
9983  20.918076  106.638658           0    24.505724  -114      -96.271155  17.728845
6044  16.092370  108.141370           9  2457.200022  -107     -121.635713  14.635713
9367  20.894690  106.592545           0    38.123787   -89     -102.251051  13.251051
9387  20.917776  106.638645           1    14.416944  -119     -105.926540  13.073460
42    16.073327  108.149796           6   304.388073   -90     -102.739916  12.739916
6011  16.092370  108.141370           9  2457.200022  -109     -121.635713  12.635713
9973  20.918076  106.638658           0    24.505724   -84      -96.271155  12.271155
5256  16.060720  108.162170          11  1169.033888   -96     -106.340547  10.340547

sans les points avec std rssi > 5 :
R²   : 0.9176 ± 0.0059  MAE  : 1.92 dBm  RMSE : 2.92 dBm
max error : 12.959961, error std : 1.24768

sans std rssi > 10 : 
R²   : 0.9136 ± 0.0075  MAE  : 1.97 dBm  RMSE : 2.99 dBm
max = 31.63, std = 1.38

sans std rssi >15:
R²   : 0.9119 ± 0.0104  MAE  : 1.97 dBm  RMSE : 3.02 dBm
meme stats.

sans std rssi > 20v et >18 : comme le model de base sans removal
R²   : 0.9257 ± 0.0066  MAE  : 1.95 dBm  RMSE : 2.98 dBm
meme stats max, std

sans les 3 pires points de la meme position : (6009, 6043, 6044 : 
6009  16.092370  108.141370           9  2457.200022   -90     -121.635713  31.635713
6043  16.092370  108.141370           9  2457.200022   -95     -124.273468  29.273468
9983  20.918076  106.638658           0    24.505724  -114      -96.271155  17.728845
6044  16.092370  108.141370           9  2457.200022  -107     -121.635713  14.635713)
R²   : 0.9266 ± 0.0092  MAE  : 1.95 dBm  RMSE : 2.96 dBm
error max 17.7, std =1.314

sans 9983,6011,6041,9973,9975: 
            lat         lon  gateway_id      distance  rssi  predicted_rssi      error
9983  20.918076  106.638658           0     24.505724  -114      -96.270475  17.729525
6011  16.092370  108.141370           9   2457.200022  -109     -124.352941  15.352941
9387  20.917776  106.638645           1     14.416944  -119     -106.074174  12.925826
9367  20.894690  106.592545           0     38.123787   -89     -101.901098  12.901098
42    16.073327  108.149796           6    304.388073   -90     -102.453219  12.453219
6041  16.092370  108.141370           9   2457.200022  -112     -124.352941  12.352941
9973  20.918076  106.638658           0     24.505724   -84      -96.270475  12.270475
5256  16.060720  108.162170          11   1169.033888   -96     -106.327228  10.327228
9975  20.918076  106.638658           0     24.505724   -86      -96.270475  10.270475
R²   : 0.9269 ± 0.0056  MAE  : 1.95 dBm  RMSE : 2.95 dBm
max = 17.72, std = 1.316

sans 
        eps = 1e-6
        mask = (
            (
                (abs(df["lat"] - 16.092370) < eps) &
                (abs(df["lon"] - 108.141370) < eps) &
                (df["gateway_id"] == 9) 
                # (df["rssi"].isin([-90, -95, -109, -112,-107]))
            )
            |
            (
                (abs(df["lat"] - 20.918076) < eps) &
                (abs(df["lon"] - 106.638658) < eps) &
                (df["gateway_id"] == 0)
                # (df["rssi"].isin([-114, -84,-86]))
            )
        )
R²   : 0.9270 ± 0.0079  MAE  : 1.94 dBm  RMSE : 2.94 dBm
std 1.272., max 13

sans : 
        eps = 1e-6
        mask = (
            (
                (abs(df["lat"] - 16.092370) < eps) &
                (abs(df["lon"] - 108.141370) < eps) &
                (df["gateway_id"] == 9) &
                (df["rssi"].isin([-90, -95, -109, -112,-107]))
            )
            |
            (
                (abs(df["lat"] - 20.918076) < eps) &
                (abs(df["lon"] - 106.638658) < eps) &
                (df["gateway_id"] == 0) &
                (df["rssi"].isin([-114, -84]))
            )
        )
R²   : 0.9285 ± 0.0065  MAE  : 1.93 dBm  RMSE : 2.92 dBm
std 1.291, max 13.39

DONC : For duplicate measurements presenting physically inconsistent RSSI values, only the extreme outliers were removed while the remaining observations were preserved.
Vu les écarts :

24.5 m : [-114, -106, -86, -84]
2457 m : [-112, -109, -107, -95, -90]

on peut raisonnablement considérer que les extrêmes sont des mesures corrompues ou prises dans des conditions exceptionnelles.

MODEL FINAL R²   : 0.9285 ± 0.0065

ensuite :
To facilitate deployment, the final prediction engine was separated from the training framework. The inference module only loads the pre-trained model and a lightweight spatial reference database, computes the required environmental and nearest-neighbor features for a queried location, and directly outputs the predicted RSSI value. This modular design enables efficient integration into interactive radio coverage mapping applications without requiring any retraining or data preprocessing steps.


FINAL FAETURES IMPORTANCES : 
R²   : 0.9285 ± 0.0065  MAE  : 1.93 dBm  RMSE : 2.92 dBm
Feature importances:
  residential_ratio: 0.159034
  gateway: 0.118775
  neighbor_rssi_weighted_mean: 0.082913
  frequency: 0.078519
  neighbor_rssi_mean: 0.061081
  rssi_closest_point: 0.058920
  elevation_angle: 0.047367
  spreading_factor: 0.034238
  log_distance_3d: 0.033997
  elevation: 0.030865
  gw_elevation: 0.012601
  terrain_mean: 0.011299
  slope: 0.010232
  terrain_max: 0.008701
  roughness: 0.005799
  closest_to_gw_distance: 0.005342
  neighbor_gw_distance_mean: 0.005239
  terrain_min: 0.004956
  distance_3d: 0.003900
  max_obstruction: 0.002811
  mean_fresnel_clearance: 0.002572
  neighbor_rssi_std: 0.002101
  angle: 0.001363

  distance_closest_point: 0.000803
  delta_lon: 0.000706
  neighbor_distance_mean: 0.000704
  terrain_std: 0.000610
  fresnel_obstruction_ratio: 0.000558
  terrain_range: 0.000426
  min_fresnel_clearance: 0.000394
  delta_lat: 0.000340
  delta_elevation: 0.000267

  sans les derniers : R²   : 0.9279 ± 0.0067  MAE  : 1.94 dBm  RMSE : 2.94 dBm

  


  Predicting...
                   count          mean          std           min           25%           50%           75%           max
gateway                                                                                                                  
24e124fffef4778e  1291.0    232.628779   763.195559      1.131558     17.413895     48.318235    220.689960   5476.419208
7076ff0054070418   190.0    758.961589  1865.372239      1.571779      8.966111     14.625930     23.900619   5468.164239
7276ff002e0507da   583.0    467.370623   247.886966     11.645010    305.785812    462.023808    592.980507   1411.228610
7276ff002e06029f   191.0    530.019026   549.651280     21.348221    292.275755    410.260743    710.953931   7018.613287
7276ff002e061f5b  1787.0   6881.145457  2391.924200     90.305479   5973.063367   7478.251835   8104.060107  15974.728667
7276ff002e062cf2  1131.0  14553.825423  2380.566483  10173.549560  13561.480004  14163.650651  14911.654134  26892.408704
a840411eebb44150   288.0    205.432793   146.749151     15.215815     76.033469    183.381203    303.261881    766.124181
a84041ffff1ec39f   151.0   5065.677962  3324.413126     16.141583   1018.189228   7498.434153   7542.444645   7734.183798
ac1f09fffe00ab20    10.0   1007.465172  2593.339818     16.570966     56.951100     90.051577    130.644039   8326.530994
ac1f09fffe00ab25   106.0   1664.394094  2180.702884    132.613034    295.835031    553.607214   2457.200022  10701.646765
ac1f09fffe06fcf2    63.0   2960.849783  1478.939846    972.906173   2459.801394   2663.733708   3229.040820   8300.174887
ac1f09fffe0fd629  4397.0    801.112026   616.272306    193.746433    677.903765    684.121939    692.904107  16435.696759
ac1f09fffe0fd63b    15.0  13437.321802   795.547071  12378.693654  12784.799792  13253.984240  14235.344233  14513.705819


le coverage n'est pas le meme pour chaque gateway logiquement : je selectionne la gateway en fonction de la gateway du point le plus proche. ensuite si le point en lui meme est trop loin de la gateway par rapport a son coverage je predis direct -120. si point proche <150m alors on renvoie direct son rssi (pas model mais app inference opti)

nouvelles données test: nouvelle gateway donc ca prend la gateway du point le plus proche. il y a 2 mesure par lat/lon pour chaque gateway : on garde l'erreur la plus basse : on passe de MAE: 9.19e, RMSE: 12.41 à MAE : 8.72 dB, RMSE : 11.74 dB
on enleve la gateway qu'on connait pas : MAE : 7.51 dB, RMSE: 11.26 dB
on enleve gateway inconnue + duplicates : MAE pred1: 5.73 dB RMSE pred1: 8.31 dB
on corrige le predict : MAE pred2: 3.31 dB RMSE pred2: 4.60 dB (800 nouvelles mesures)
