"""Out-of-sample counterpart of map_level.py: leave-sector-out recall and Lee-Liu criterion of the
random-negative Random Forest for each positive-to-negative ratio (ten random draws, scores averaged),
to compare with the in-sample map-level agreement of the same models, with paired sector-bootstrap
differences with respect to the nested PU-RF of revision_analyses.py (results/06)."""
import numpy as np
import pandas as pd

from common import FEATS, bootstrap, load, metrics, protocol_lso, pu_training_set, results_dir, rf

OUT = results_dir("results")
d, folds = protocol_lso(load())
rows, oof = [], []
for name, ratio in {"1:0.5": 0.5, "1:1": 1, "1:2": 2, "1:4.7 (PU count)": None, "all unlabeled (1:6.7)": "all"}.items():
    s_all, sc_all = [], []
    for tr, va in folds:
        A, B = d.iloc[tr], d.iloc[va]
        p, u = A[A.classes == 1], A[A.classes == 0]
        if ratio == "all":
            draws = [u]
        else:
            k = int((pu_training_set(A)[1] == 0).sum()) if ratio is None else int(round(ratio * len(p)))
            draws = [u.sample(min(k, len(u)), random_state=sd) for sd in range(10)]
        sc = np.mean([rf(i).fit(pd.concat([p[FEATS], n[FEATS]]), np.r_[np.ones(len(p)), np.zeros(len(n))])
                      .predict_proba(B[FEATS])[:, 1] for i, n in enumerate(draws)], axis=0)
        s_all.append(B.classes.values); sc_all.append(sc)
        oof.append(pd.DataFrame(dict(method=name, group=B.group.values, s=B.classes.values, score=sc, yhat=sc >= 0.5)))
    m = metrics(np.concatenate(s_all), np.concatenate(sc_all))
    rows.append(dict(model=name, **m)); print(name, {k: round(v, 3) for k, v in m.items()}, flush=True)
pd.DataFrame(rows).to_csv(OUT / "17_ratio_leave_sector_out.csv", index=False)
pu = pd.read_csv(OUT / "06_out_of_fold_predictions.csv.gz", dtype={"group": str})
pu = pu[(pu.protocol == "leave-sector-out") & (pu.method == "PU-RF")][["method", "group", "s", "score", "yhat"]]
both = pd.concat([pu] + oof).assign(group=lambda x: x.group.astype(str), yhat=lambda x: x.yhat.astype(bool))
_, diffs = bootstrap(both, "leave-sector-out", "PU-RF", keys=("auc_pu", "recall", "lee_liu"))
diffs.to_csv(OUT / "19_ratio_lso_paired_differences.csv", index=False)
print(diffs.round(3).to_string(index=False))
