"""Stability of the PU map across spy draws (seeds 0-9), for comparison with the variability of the
random-negative maps across random draws (map_level.py)."""
import numpy as np
import pandas as pd

import map_level as ml  # reuses the raster stack, post-processing and metrics
from common import pu_training_set, results_dir, rf

OUT = results_dir("results")
maps, rows = [], []
for seed in range(10):
    X, y = pu_training_set(ml.Dstar, seed=seed)
    m = ml.predict(rf(seed).fit(X, y)); maps.append(m)
    rows.append(ml.metrics(m, "PU-RF (Spy repeated with seed)", seed))
jac = [ (maps[i] & maps[j]).sum() / (maps[i] | maps[j]).sum() for i in range(10) for j in range(i + 1, 10)]
res = pd.DataFrame(rows).assign(jaccard_between_seeds_mean=np.mean(jac))
res.to_csv(OUT / "18_pu_map_stability.csv", index=False)
print(res[["predicted_ha", "area_recall", "area_precision", "Fpb"]].describe().round(3).loc[["mean", "min", "max"]])
print("Jaccard between PU maps (spy seeds):", round(np.mean(jac), 3), round(min(jac), 3))
