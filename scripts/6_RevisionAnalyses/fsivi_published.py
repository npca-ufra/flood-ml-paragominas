"""Published FSIVI raster versus the sample-level index of Table S2 (Reviewer 3, comment 3.5).

Table S2 recomputes the index at the sample points of D* with min-max normalization over the sample set,
whereas Eq. 2 normalizes each predictor over the masked urban raster. The published FSIVI raster is sampled at
the same points and compared with the sample-level index and with the out-of-fold Random Forest probability.
"""
import numpy as np
import pandas as pd
import rasterio
from rasterio.warp import transform
from scipy.stats import spearmanr

from common import DATA, FEATS, HERE, load, protocol_5fold, results_dir, rf

FSIVI_TIF = HERE.parent / "files" / "heat_map_flood_risk_postClassif.tif"   # from Zenodo (10.5281/zenodo.21227777)
OUT = results_dir("results")
d = load()
Dstar, _, labels, folds, _ = protocol_5fold(d)
y = labels.loc[Dstar.index].values
p_rf = np.zeros(len(Dstar))
for tr, va in folds:
    p_rf[va] = rf().fit(Dstar.iloc[tr][FEATS], y[tr]).predict_proba(Dstar.iloc[va][FEATS])[:, 1]

# sample-level index of Table S2 (fsivi_checks.py)
imp = pd.read_csv(DATA / "feature_importance_flood.csv")[FEATS].iloc[0]
W = imp / imp.sum()
SIGN = {f: -1 for f in FEATS} | {"twi": 1}
lo, hi = d[FEATS].min(), d[FEATS].max()
n = (Dstar[FEATS] - lo) / (hi - lo)
f_sample = sum(W[f] * (n[f] if SIGN[f] > 0 else 1 - n[f]) for f in FEATS).values

with rasterio.open(FSIVI_TIF) as r:
    xs, ys = transform("EPSG:4326", r.crs, Dstar.lon.values, Dstar.lat.values)
    f_pub = np.array([v[0] for v in r.sample(zip(xs, ys))], dtype=float)
    if r.nodata is not None:
        f_pub[f_pub == r.nodata] = np.nan
ok = np.isfinite(f_pub)
rows = [("Sample points of D*", len(Dstar)),
        ("Sample points inside the published FSIVI domain", int(ok.sum())),
        ("Spearman correlation, published FSIVI vs sample-level FSIVI of Table S2", spearmanr(f_pub[ok], f_sample[ok])[0]),
        ("Spearman correlation, published FSIVI vs Random Forest probability", spearmanr(f_pub[ok], p_rf[ok])[0]),
        ("Spearman correlation, sample-level FSIVI vs Random Forest probability (same points)", spearmanr(f_sample[ok], p_rf[ok])[0])]
pd.DataFrame(rows, columns=["Quantity", "Value"]).to_csv(OUT / "23_fsivi_published_vs_sample.csv", index=False)
print(pd.DataFrame(rows).to_string(index=False, header=False))
