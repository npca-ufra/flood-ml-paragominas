"""FSIVI checks (Reviewer 2, comment 4; Reviewer 3, comment 5) at the sample points of D*.

Same computation as section 8 of notebook 3.4 (Table S2), with the exact importance weights read
from feature_importance_flood.csv instead of rounded values, plus:
  * direction check: sign of the association of each predictor with the original sector labels,
    compared with the direction assigned a priori in Eq. 4;
  * discrimination of the original sector samples (AUC_PU) by the FSIVI and by the Random Forest.
"""
import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.metrics import cohen_kappa_score, roc_auc_score

from common import DATA, FEATS, load, protocol_5fold, results_dir, rf

OUT = results_dir("results")
d = load()
Dstar, _, labels, folds, _ = protocol_5fold(d)
y = labels.loc[Dstar.index].values
s = Dstar.classes.values

p_rf = np.zeros(len(Dstar))
for tr, va in folds:
    p_rf[va] = rf().fit(Dstar.iloc[tr][FEATS], y[tr]).predict_proba(Dstar.iloc[va][FEATS])[:, 1]

imp = pd.read_csv(DATA / "feature_importance_flood.csv")[FEATS].iloc[0]
W = imp / imp.sum()
SIGN = {f: -1 for f in FEATS} | {"twi": 1}
lo, hi = d[FEATS].min(), d[FEATS].max()


def fsivi(w, X=Dstar):
    n = (X[FEATS] - lo) / (hi - lo)
    return sum(w[f] * (n[f] if SIGN[f] > 0 else 1 - n[f]) for f in FEATS).values


f = fsivi(W)
rows = [("Spearman correlation, FSIVI vs Random Forest probability", spearmanr(f, p_rf)[0]),
        ("ROC-AUC of FSIVI for samples classified as flood-prone by the Random Forest (p >= 0.5)",
         roc_auc_score(p_rf >= 0.5, f))]
for q, name in [(4, "Quartile"), (5, "Quintile")]:
    cf = pd.qcut(f, q, labels=False)
    cr = pd.qcut(pd.Series(p_rf).rank(method="first"), q, labels=False).values
    rows += [(f"{name} classes, FSIVI vs Random Forest: quadratic-weighted kappa",
              cohen_kappa_score(cf, cr, weights="quadratic")),
             (f"{name} classes: agreement within one class", (abs(cf - cr) <= 1).mean())]
rows.append(("Spearman correlation, importance-weighted vs equal-weighted FSIVI",
             spearmanr(f, fsivi(pd.Series(1 / 6, index=FEATS)))[0]))
rng = np.random.default_rng(0)
alpha = W.values * 50
rho = [spearmanr(f, fsivi(pd.Series(rng.dirichlet(alpha), index=FEATS)))[0] for _ in range(1000)]
rows += [("Spearman correlation under 1,000 random perturbations of the weights: median", np.median(rho)),
         ("Spearman correlation under 1,000 random perturbations of the weights: minimum", np.min(rho)),
         ("ROC-AUC against the original sector labels (labeled vs unlabeled): FSIVI", roc_auc_score(s, f)),
         ("ROC-AUC against the original sector labels (labeled vs unlabeled): Random Forest (out-of-fold)",
          roc_auc_score(s, p_rf))]
table = pd.DataFrame(rows, columns=["Quantity", "Value"])
table.to_csv(OUT / "08_table_S2_fsivi.csv", index=False)

direction = pd.DataFrame({f_: dict(weight=W[f_], direction_in_FSIVI="direct" if SIGN[f_] > 0 else "inverse",
                                   spearman_with_sector_label=spearmanr(Dstar[f_], s)[0],
                                   spearman_with_rf_probability=spearmanr(Dstar[f_], p_rf)[0]) for f_ in FEATS}).T
direction.to_csv(OUT / "09_fsivi_direction_check.csv")
pd.set_option("display.width", 200, "display.max_colwidth", 100)
print("weights:", W.round(4).to_dict())
print(table.round(3).to_string(index=False))
print(direction)
