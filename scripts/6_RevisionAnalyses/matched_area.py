"""Comparison at an equal predicted area (Table 5 and Sect. 4.4): each model is evaluated with the same
share of samples predicted as positive as the PU-RF (its share at the 0.5 threshold), so that recall and the
Lee-Liu criterion no longer depend on each model's default operating point. Also reports the maximum Lee-Liu
over all thresholds. Uses the out-of-fold predictions of revision_analyses.py."""
import numpy as np
import pandas as pd

from common import recall_at_fraction, results_dir

OUT = results_dir("results")
oof = pd.read_csv(OUT / "06_out_of_fold_predictions.csv.gz", dtype={"group": str})
REF = "PU-RF"


def at_share(x, q):
    r = recall_at_fraction(x.s.values, x.score.values, q)
    return r, r ** 2 / q


def max_lee_liu(x):
    qs = np.arange(0.05, 0.96, 0.01)
    v = [recall_at_fraction(x.s.values, x.score.values, q) ** 2 / q for q in qs]
    i = int(np.argmax(v))
    return v[i], qs[i]


rows, diffs = [], []
for prot, P in oof.groupby("protocol", sort=False):
    q = (P[P.method == REF].score >= 0.5).mean()
    groups = P.group.unique()
    parts = {k: g for k, g in P.groupby(["method", "group"])}
    rng = np.random.default_rng(0)
    draws = [rng.choice(groups, len(groups), replace=True) for _ in range(1000)]
    boot_ref = []
    for pick in draws:
        x = pd.concat([parts[(REF, g)] for g in pick]); boot_ref.append(at_share(x, q)[1])
    for m, x in P.groupby("method", sort=False):
        r, ll = at_share(x, q); mx, qmx = max_lee_liu(x)
        b = []
        for pick in draws:
            xb = pd.concat([parts[(m, g)] for g in pick]); b.append(at_share(xb, q)[1])
        b = np.array(b); lo, hi = np.quantile(b, [0.025, 0.975])
        rows.append(dict(protocol=prot, method=m, equal_share=q, recall_equal_share=r, lee_liu_equal_share=ll,
                         lee_liu_equal_share_lo=lo, lee_liu_equal_share_hi=hi, max_lee_liu=mx, share_at_max=qmx))
        if m != REF:
            dd = np.array(boot_ref) - b
            diffs.append(dict(protocol=prot, method=m, diff_lee_liu_equal_share=at_share(P[P.method == REF], q)[1] - ll,
                              lo=np.quantile(dd, 0.025), hi=np.quantile(dd, 0.975), share_le_0=(dd <= 0).mean()))
pd.DataFrame(rows).to_csv(OUT / "11_equal_predicted_area.csv", index=False)
pd.DataFrame(diffs).to_csv(OUT / "12_equal_area_paired_differences.csv", index=False)
pd.set_option("display.width", 250, "display.max_colwidth", 60)
print(pd.DataFrame(rows).round(3).to_string(index=False)); print(pd.DataFrame(diffs).round(3).to_string(index=False))
