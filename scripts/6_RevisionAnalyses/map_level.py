"""Map-level effect of the labeling scheme (Sect. 4.4, Table S6). The same Random Forest is trained on D* with (i) the PU labels of the paper and
(ii) the original positives plus pseudo-negatives drawn at random from the unlabeled samples at several
ratios, and applied to the whole study area (predictor stack spatial_data_raster_flood.tif, Zenodo).
All maps receive the post-processing of the paper: urban mask (MapBiomas class 24), 3x3 focal mode and a
3,000 m2 minimum mapping unit. Area metrics use the urban portion of the CPRM/SGB flood sectors."""
import numpy as np
import pandas as pd
import rasterio
from rasterio.features import rasterize
from scipy import ndimage

import geopandas as gpd

from common import DATA, FEATS, load, protocol_5fold, results_dir, rf

OUT = results_dir("results")
BAND = {"distance": 1, "elevation": 2, "slope": 3, "ksat": 4, "hand": 5, "twi": 6}
RATIOS = {"1:0.5": 0.5, "1:1": 1, "1:2": 2, "1:4.7 (PU count)": None, "all unlabeled (1:6.7)": "all"}
SEEDS = range(10)

with rasterio.open(DATA / "spatial_data_raster_flood.tif") as r:
    X = np.stack([r.read(BAND[f]) for f in FEATS], -1).astype("float32")
    urban = r.read(7) == 24
    T, shape = r.transform, (r.height, r.width)
    lat = r.xy(np.arange(r.height), np.zeros(r.height, int))[1]
px_ha = np.broadcast_to(((abs(T.a) * 111320 * np.cos(np.radians(lat)))[:, None] * abs(T.e) * 110574 / 1e4), shape)
valid = urban & np.isfinite(X).all(-1)
s = gpd.read_file(f"zip://{DATA / 'risk_sectorization_and_streams.zip'}!risk_sectorization/risk_sectorization_PGM.shp",
                  encoding="latin1").to_crs(4326)
s = s[s.tipolo_g1.str.startswith("Inunda")]   # CPRM/SGB process type: the 18 river-flood (Inundacao) sectors; the 3 Alagamento sectors are excluded, as in the GEE scripts
ref = (rasterize(((g, 1) for g in s.geometry), out_shape=shape, transform=T) == 1) & urban
ref_ha = px_ha[ref].sum()
Xv = X[valid]


def postprocess(m):
    m = ndimage.generic_filter(m.astype(np.uint8), lambda w: np.bincount(w.astype(int), minlength=2).argmax(), size=3) == 1
    m &= urban
    lab, n = ndimage.label(m)
    area = ndimage.sum(px_ha, lab, range(1, n + 1))
    keep = np.r_[False, area >= 0.3]  # 3,000 m2
    return keep[lab]


def predict(model):
    m = np.zeros(shape, bool)
    m[valid] = model.predict_proba(Xv)[:, 1] >= 0.5
    return postprocess(m)


def metrics(m, name, seed=None):
    P, I = px_ha[m].sum(), px_ha[m & ref].sum()
    return dict(model=name, seed=seed, predicted_ha=P, inside_ha=I, area_recall=I / ref_ha, area_precision=I / P if P else np.nan,
                Fpb=2 * I / (ref_ha + P - I), share_urban=P / px_ha[urban].sum())


d = load()
Dstar, _, labels, _, _ = protocol_5fold(d)
pos, unl = Dstar[Dstar.classes == 1], Dstar[Dstar.classes == 0]
n_rn = int((labels.loc[unl.index] == 0).sum())
if __name__ == "__main__":
    rows, maps = [], {}
    pu_map = predict(rf().fit(Dstar[FEATS], labels.loc[Dstar.index]))
    maps["PU"] = pu_map
    rows.append(metrics(pu_map, "PU-RF (paper labels)"))
    for name, ratio in RATIOS.items():
        for seed in SEEDS:
            if ratio == "all":
                neg = unl
            else:
                k = n_rn if ratio is None else int(round(ratio * len(pos)))
                neg = unl.sample(min(k, len(unl)), random_state=seed)
            X_ = pd.concat([pos[FEATS], neg[FEATS]]); y_ = np.r_[np.ones(len(pos)), np.zeros(len(neg))]
            m = predict(rf(seed).fit(X_, y_))
            maps[(name, seed)] = m
            rows.append(metrics(m, f"RF + random negatives {name}", seed))
            if ratio == "all":
                break
        print("done", name, flush=True)
    res = pd.DataFrame(rows)
    res.to_csv(OUT / "15_map_level_metrics.csv", index=False)

    # variability across random draws and agreement with the PU map (Jaccard)
    def jac(a, b):
        return (a & b).sum() / max((a | b).sum(), 1)
    agree = []
    for name in RATIOS:
        ms = [maps[k] for k in maps if isinstance(k, tuple) and k[0] == name]
        pairs = [jac(ms[i], ms[j]) for i in range(len(ms)) for j in range(i + 1, len(ms))]
        agree.append(dict(model=name, jaccard_between_draws_mean=np.mean(pairs) if pairs else np.nan,
                          jaccard_with_PU_mean=np.mean([jac(m, pu_map) for m in ms])))
    pd.DataFrame(agree).to_csv(OUT / "16_map_level_agreement.csv", index=False)
    summ = res.groupby("model", sort=False).agg(["mean", "min", "max"]).drop(columns="seed")
    pd.set_option("display.width", 250)
    print(f"reference (urban sectors) = {ref_ha:.2f} ha; urban area = {px_ha[urban].sum():.1f} ha")
    print(summ[["predicted_ha", "area_recall", "area_precision", "Fpb", "share_urban"]].round(3).to_string())
    print(pd.DataFrame(agree).round(3).to_string(index=False))
