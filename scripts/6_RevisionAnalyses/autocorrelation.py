"""Spatial autocorrelation range versus the block design (Sect. 3.4.3). The correlogram is computed on a random subset of 5,000 points.

Empirical correlogram (Pearson correlation between pairs of standardized values, per 50 m distance
bin) of the out-of-fold residuals of the PU Random Forest (original sector label minus out-of-fold
probability, 5-fold spatial CV with the labels of the paper) and of the predictors, on D*.
The practical range is the first lag at which the correlation falls below 0.1.
"""
import numpy as np
import pandas as pd
from scipy.spatial.distance import pdist

from common import FEATS, load, protocol_5fold, results_dir, rf

OUT = results_dir("results")
d = load()
Dstar, _, labels, folds, _ = protocol_5fold(d)
p = np.zeros(len(Dstar))
for tr, va in folds:
    p[va] = rf().fit(Dstar.iloc[tr][FEATS], labels.loc[Dstar.index[tr]]).predict_proba(Dstar.iloc[va][FEATS])[:, 1]
Dstar = Dstar.assign(residual=Dstar.classes.values - p,
                     x=Dstar.lon * 111320 * np.cos(np.radians(Dstar.lat.mean())), y=Dstar.lat * 110574)
sub = Dstar.sample(5000, random_state=0)
dist = pdist(sub[["x", "y"]].values)
bins = np.arange(0, 2001, 50)
ib = np.digitize(dist, bins) - 1
iu = np.triu_indices(len(sub), 1)
cor = {}
for v in ["residual"] + FEATS:
    z = ((sub[v] - sub[v].mean()) / sub[v].std()).values
    prod = pd.Series(z[iu[0]] * z[iu[1]])
    cor[v] = prod.groupby(ib).mean().reindex(range(len(bins) - 1)).values
cor = pd.DataFrame(cor, index=bins[:-1] + 25)
rng = {v: int(cor.index[np.argmax(cor[v].values < 0.1)]) if (cor[v] < 0.1).any() else None for v in cor}
cor.to_csv(OUT / "10_correlogram.csv")
pd.Series(rng).to_csv(OUT / "10_practical_range_m.csv")
print("practical range (m, r < 0.1):", rng)
print(cor.loc[:500].round(2))
