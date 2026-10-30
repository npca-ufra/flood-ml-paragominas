"""Shared functions for the revision analyses (ENVSOFT-D-26-02946, first revision).

Reproduces the labeling step of notebook 3.1 and defines the two evaluation protocols:
  A) the paper's 5-fold spatial cross-validation on the training partition D*;
  B) leave-sector-out on the full sample set.
All metrics are computed against the ORIGINAL labels (1 = inside a CPRM/SGB flood sector,
0 = unlabeled), so methods trained with different labeling schemes are scored on equal terms.
"""
import json
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans, SpectralClustering
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score, silhouette_score
from sklearn.model_selection import GroupKFold, train_test_split
from sklearn.naive_bayes import GaussianNB
from sklearn.preprocessing import StandardScaler

HERE = Path(__file__).resolve().parent
DATA = HERE.parent / "files"  # scripts/files in the repository
FEATS = ["ksat", "slope", "distance", "elevation", "hand", "twi"]


def results_dir(name):
    out = HERE / name
    out.mkdir(exist_ok=True)
    return out


# ------------------------------------------------------------------------- labeling and model
def spy_scores(X_pos, X_unl, seed=42, spy_frac=0.2):
    """Spy step of notebook 3.1: returns spy probabilities and unlabeled probabilities."""
    X_spy, X_lab = train_test_split(X_pos, test_size=1 - spy_frac, random_state=seed,
                                    stratify=np.ones(len(X_pos)))
    X = np.vstack([X_lab, X_unl, X_spy])
    y = np.r_[np.ones(len(X_lab)), np.zeros(len(X_unl) + len(X_spy))]
    nb = GaussianNB().fit(X, y)
    return nb.predict_proba(X_spy)[:, 1], nb.predict_proba(X_unl)[:, 1]


def threshold(p_spy, rule="paper"):
    """'paper': mu-sigma, replaced by Q1 if more than 10% of the spies fall below it;
    'musigma': mu-sigma only; float q: q-quantile of the spy scores (e.g. 0.10)."""
    mu_sigma = p_spy.mean() - p_spy.std()
    if rule == "paper":
        return np.percentile(p_spy, 25) if (p_spy < mu_sigma).mean() > 0.10 else mu_sigma
    if rule == "musigma":
        return mu_sigma
    return np.percentile(p_spy, 100 * rule)


def spy_labels(X_pos, X_unl, seed=42, rule="paper"):
    p_spy, p_unl = spy_scores(X_pos, X_unl, seed)
    tau = threshold(p_spy, rule)
    info = dict(n_spies=len(p_spy), mu_sigma=p_spy.mean() - p_spy.std(), q1=np.percentile(p_spy, 25),
                below_mu_sigma=(p_spy < p_spy.mean() - p_spy.std()).mean(), tau=tau)
    new = (p_unl >= tau).astype(int)
    info.update(promoted=int(new.sum()), reliable_negatives=int((new == 0).sum()))
    return new, info


def pu_training_set(A, seed=42, rule="paper", feats=FEATS):
    """X, y for the classifier: original positives (1) + unlabeled relabeled by the Spy step."""
    p, u = A[A.classes == 1], A[A.classes == 0]
    new, _ = spy_labels(p[feats].values, u[feats].values, seed, rule)
    return pd.concat([p[feats], u[feats]]), np.r_[np.ones(len(p)), new]


def rf(seed=42):
    """sklearn equivalent of ee.Classifier.smileRandomForest(numberOfTrees=100)."""
    return RandomForestClassifier(n_estimators=100, random_state=seed, n_jobs=-1)


# ------------------------------------------------------------------------- data and protocols
def load():
    """Sample set in the row order of notebook 3.1 (shuffle with random_state=42)."""
    d = pd.read_csv(DATA / "flood_dataset.csv").sample(frac=1, random_state=42).reset_index(drop=True)
    ll = np.array([json.loads(g)["coordinates"] for g in d[".geo"]])
    d["lon"], d["lat"] = ll[:, 0], ll[:, 1]
    return d


def protocol_5fold(d):
    """Notebook 3.1: K-Means feature-stratified 85/15 holdout, Spy on D*, Spectral Clustering
    (10 groups, lon/lat) + GroupKFold(5). Returns D* (with 'group'), test, paper labels, folds, info."""
    Z = StandardScaler().fit_transform(d[FEATS])
    km = lambda k: KMeans(k, init="k-means++", random_state=42, n_init="auto").fit_predict(Z)
    sil = {k: silhouette_score(Z, km(k)) for k in range(5, 11)}
    k_opt = max(sil, key=sil.get)
    key = d.classes.astype(str) + "_" + pd.Series(km(k_opt)).astype(str)
    vc = key.value_counts()
    for bad in vc[vc < 2].index:
        key[key == bad] = vc[vc >= 2].idxmin()
    train, test = train_test_split(d, test_size=0.15, random_state=42, stratify=key)
    pos, unl = train[train.classes == 1], train[train.classes == 0]
    new, info = spy_labels(pos[FEATS].values, unl[FEATS].values)
    labels = pd.concat([pd.Series(1, index=pos.index), pd.Series(new, index=unl.index)])
    Dstar = pd.concat([pos, unl])  # positives first, as in cell 21 of notebook 3.1
    Dstar["group"] = SpectralClustering(10, random_state=42, assign_labels="discretize",
                                        affinity="nearest_neighbors", n_neighbors=10
                                        ).fit_predict(Dstar[["lon", "lat"]].values)
    folds = list(GroupKFold(5).split(Dstar, groups=Dstar.group))
    info["silhouette_k"] = k_opt
    return Dstar, test, labels, folds, info


def protocol_lso(d):
    """Leave-sector-out: each sample joins its nearest CPRM/SGB sector containing positives
    (sector + Voronoi neighbourhood); each sector is held out once."""
    s = gpd.read_file(f"zip://{DATA / 'risk_sectorization_and_streams.zip'}!risk_sectorization/risk_sectorization_PGM.shp",
                      encoding="latin1").to_crs(31983)
    pts = gpd.GeoDataFrame(geometry=gpd.points_from_xy(d.lon, d.lat), crs=4326).to_crs(31983)
    near = gpd.sjoin_nearest(pts, s[["num_setor", "geometry"]], how="left")
    near = near[~near.index.duplicated()]
    with_pos = near.loc[d.classes.values == 1, "num_setor"].unique()
    near = gpd.sjoin_nearest(pts, s[s.num_setor.isin(with_pos)][["num_setor", "geometry"]], how="left")
    d = d.copy()
    d["group"] = near[~near.index.duplicated()]["num_setor"].values
    folds = [(np.where(d.group != g)[0], np.where(d.group == g)[0]) for g in d.group.unique()]
    return d, folds


# ------------------------------------------------------------------------- metrics
def metrics(s, score, yhat=None):
    """PU-appropriate metrics against the original labels s.
    auc_pu  : labeled-vs-unlabeled ROC-AUC (ranks models; absolute value biased low, Li et al. 2022)
    recall  : recall of sector samples at the operating point (score >= 0.5 unless yhat given)
    lee_liu : recall^2 / P(yhat = 1)  (Lee and Liu 2003), proportional to precision x recall
    recall_topXX : recall of sector samples among the XX% highest scores (fixed predicted area)"""
    s, score = np.asarray(s), np.asarray(score)
    yhat = score >= 0.5 if yhat is None else np.asarray(yhat, bool)
    rec, ppos = yhat[s == 1].mean(), yhat.mean()
    m = dict(auc_pu=roc_auc_score(s, score), recall=rec, pred_pos_rate=ppos,
             lee_liu=rec ** 2 / ppos if ppos > 0 else np.nan)
    for q in (0.05, 0.10, 0.20):
        m[f"recall_top{int(q * 100)}"] = recall_at_fraction(s, score, q)
    return m


def recall_at_fraction(s, score, q):
    """Recall of the positives within the q fraction of highest scores. Samples tied with the
    score at the cut-off are credited fractionally (expected value under random tie-breaking),
    because Random Forest probabilities take few distinct values."""
    k = int(round(q * len(s)))
    t = np.sort(score)[::-1][k - 1]
    above, tied = score > t, score == t
    frac = (k - above.sum()) / tied.sum()
    return (s[above].sum() + frac * s[tied].sum()) / s.sum()


def bootstrap(oof, protocol, reference, n_boot=1000, keys=("auc_pu", "lee_liu", "recall_top10")):
    """Pooled out-of-fold metrics with 95% CIs from resampling spatial groups (sectors or
    spatial clusters) and paired differences reference - method on the same draws."""
    methods = list(oof.method.unique())
    groups = oof.group.unique()
    parts = {k: g for k, g in oof.groupby(["method", "group"])}
    point = {m: metrics(x.s, x.score, x.yhat) for m, x in oof.groupby("method", sort=False)}
    rng = np.random.default_rng(0)
    boot = {m: [] for m in methods}
    for _ in range(n_boot):
        pick = rng.choice(groups, len(groups), replace=True)
        for m in methods:
            x = pd.concat([parts[(m, g)] for g in pick])
            boot[m].append(metrics(x.s, x.score, x.yhat) if 0 < x.s.mean() < 1 else None)
    rows, diffs = [], []
    for m in methods:
        b = pd.DataFrame([x for x in boot[m] if x is not None])
        row = dict(protocol=protocol, method=m)
        for k, v in point[m].items():
            row[k], (row[k + "_lo"], row[k + "_hi"]) = v, b[k].quantile([0.025, 0.975])
        rows.append(row)
        if m == reference:
            continue
        pairs = [(a, c) for a, c in zip(boot[reference], boot[m]) if a is not None and c is not None]
        for k in keys:
            dd = np.array([a[k] - c[k] for a, c in pairs])
            diffs.append(dict(protocol=protocol, reference=reference, method=m, metric=k,
                              diff=point[reference][k] - point[m][k], lo=np.quantile(dd, 0.025),
                              hi=np.quantile(dd, 0.975), share_le_0=(dd <= 0).mean()))
    return pd.DataFrame(rows), pd.DataFrame(diffs)


if __name__ == "__main__":
    s = np.r_[np.ones(100), np.zeros(900)]
    m = metrics(s, s)
    assert m["auc_pu"] == 1 and m["recall"] == 1 and abs(m["lee_liu"] - 10) < 1e-9
    assert threshold(np.array([0.0] * 20 + [0.9] * 80)) == np.percentile([0.0] * 20 + [0.9] * 80, 25)
    # ties at the cut-off: 4 positives among 10 tied scores, 5 of them inside the top 5 -> recall 2/4
    assert abs(recall_at_fraction(np.r_[np.ones(4), np.zeros(6)], np.full(10, 0.5), 0.5) - 0.5) < 1e-12
    print("ok")
