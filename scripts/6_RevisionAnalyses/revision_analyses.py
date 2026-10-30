"""Revision analyses (ENVSOFT-D-26-02946), run offline on the exported samples.

  * Random-negative ablation (Reviewer 3, comment 2 and recommendation): the same Random Forest
    trained on pseudo-negatives sampled at random from the unlabeled pool.
  * Alternative PU / presence-only approaches (Reviewer 3, comment 2): Elkan-Noto, PU bagging,
    one-class SVM, MaxEnt-type presence-background model.
  * Stronger learners on the same Spy labels (Reviewer 2, comment 5): XGBoost and SVM.
  * Threshold rules (Reviewer 3, comment 4): mu-sigma without fallback and the 10th percentile.
  * ksat (Reviewer 2, comment 3): model without ksat and out-of-sample permutation importance.
  * Nested labeling (Reviewer 2, comment 2; Reviewer 3, comment 3): Spy repeated inside each
    training fold, and the Table 2 metrics recomputed under this nested design.
Each method is evaluated under the paper's 5-fold spatial CV and under leave-sector-out.
None of these analyses changes the labels, models, tables or maps of the original study.

Run: python3 -W ignore revision_analyses.py   (results in results/, about 20 min)
"""
import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.ensemble import RandomForestClassifier
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, cohen_kappa_score, f1_score, precision_score,
                             recall_score, roc_auc_score)
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import GaussianNB
from sklearn.neighbors import NearestCentroid
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import PolynomialFeatures, StandardScaler
from sklearn.svm import SVC, OneClassSVM
from sklearn.tree import DecisionTreeClassifier
from xgboost import XGBClassifier

from common import (FEATS, bootstrap, load, metrics, protocol_5fold, protocol_lso,
                    pu_training_set, results_dir, rf, threshold)

OUT = results_dir("results")
SEEDS = range(10)
REF = "PU-RF"


# ------------------------------------------------------------------------- methods
# each returns (score, yhat) for the validation samples B, trained on A only
def pu_model(model, rule="paper", feats=FEATS):
    def run(A, B):
        X, y = pu_training_set(A, rule=rule, feats=feats)
        m = clone(model).fit(X, y)
        if hasattr(m, "predict_proba"):
            sc = m.predict_proba(B[feats])[:, 1]
            return sc, sc >= 0.5
        sc = m.decision_function(B[feats])
        return sc, sc >= 0
    return run


def pu_paper_labels(labels):
    def run(A, B):
        sc = rf().fit(A[FEATS], labels.loc[A.index]).predict_proba(B[FEATS])[:, 1]
        return sc, sc >= 0.5
    return run


def random_negatives(n_neg_rule):
    """Original positives vs pseudo-negatives sampled at random from the unlabeled pool;
    scores averaged over 10 random draws (the single draws are reported separately)."""
    def run(A, B, per_seed=None):
        p, u = A[A.classes == 1], A[A.classes == 0]
        n_neg = len(p) if n_neg_rule == "1:1" else int((pu_training_set(A)[1] == 0).sum())
        scores = []
        for seed in SEEDS:
            n = u.sample(min(n_neg, len(u)), random_state=seed)
            m = rf(seed).fit(pd.concat([p[FEATS], n[FEATS]]), np.r_[np.ones(len(p)), np.zeros(len(n))])
            scores.append(m.predict_proba(B[FEATS])[:, 1])
            if per_seed is not None:
                per_seed.append((seed, scores[-1]))
        sc = np.mean(scores, axis=0)
        return sc, sc >= 0.5
    return run


def elkan_noto(A, B):
    """Elkan and Noto (2008): g(x) = P(s=1|x) from a classifier of labeled vs unlabeled,
    c = mean g on held-out labeled samples (out-of-bag), f(x) = g(x)/c."""
    m = RandomForestClassifier(100, random_state=42, n_jobs=-1, oob_score=True,
                               min_samples_leaf=5).fit(A[FEATS], A.classes)
    c = m.oob_decision_function_[A.classes.values == 1, 1].mean()
    sc = np.clip(m.predict_proba(B[FEATS])[:, 1] / c, 0, 1)
    return sc, sc >= 0.5


def pu_bagging(A, B, n_bags=50):
    """Mordelet and Vert (2014): positives vs a bootstrap of |P| unlabeled samples, averaged."""
    p, u = A[A.classes == 1], A[A.classes == 0]
    rng = np.random.default_rng(42)
    sc = np.zeros(len(B))
    for b in range(n_bags):
        n = u.iloc[rng.integers(0, len(u), len(p))]
        m = RandomForestClassifier(20, random_state=b, n_jobs=-1).fit(
            pd.concat([p[FEATS], n[FEATS]]), np.r_[np.ones(len(p)), np.zeros(len(n))])
        sc += m.predict_proba(B[FEATS])[:, 1] / n_bags
    return sc, sc >= 0.5


def one_class_svm(A, B):
    """One-class SVM fitted on the positives; operating point = 10th percentile of the
    training-positive scores (10% omission rule)."""
    p = A[A.classes == 1]
    m = make_pipeline(StandardScaler(), OneClassSVM(nu=0.1, gamma="scale")).fit(p[FEATS])
    sc = m.decision_function(B[FEATS])
    return sc, sc >= np.percentile(m.decision_function(p[FEATS]), 10)


def maxent_type(A, B):
    """Presence-background logistic regression with linear, quadratic and product features,
    which approximates MaxEnt (Fithian and Hastie 2013; no hinge features and no L1 regularization;
    the default L2 penalty of scikit-learn is kept); 10% omission rule."""
    m = make_pipeline(StandardScaler(), PolynomialFeatures(2, include_bias=False), StandardScaler(),
                      LogisticRegression(class_weight="balanced", max_iter=5000)).fit(A[FEATS], A.classes)
    sc = m.predict_proba(B[FEATS])[:, 1]
    return sc, sc >= np.percentile(m.predict_proba(A.loc[A.classes == 1, FEATS])[:, 1], 10)


XGB = XGBClassifier(n_estimators=300, max_depth=6, learning_rate=0.1, subsample=0.8,
                    colsample_bytree=0.8, n_jobs=-1, random_state=42, verbosity=0)
SVM = make_pipeline(StandardScaler(), SVC(C=1.0, gamma="scale"))

METHODS = {
    REF: pu_model(rf()),
    "RF + random negatives (1:1)": random_negatives("1:1"),
    "RF + random negatives (same number as PU reliable negatives)": random_negatives("pu"),
    "PU-RF, mu-sigma threshold (no fallback)": pu_model(rf(), "musigma"),
    "PU-RF, 10th-percentile threshold": pu_model(rf(), 0.10),
    "PU-RF without ksat": pu_model(rf(), feats=[f for f in FEATS if f != "ksat"]),
    "PU-XGBoost": pu_model(XGB),
    "PU-SVM (RBF)": pu_model(SVM),
    "Elkan-Noto (RF)": elkan_noto,
    "PU bagging (RF)": pu_bagging,
    "One-class SVM": one_class_svm,
    "MaxEnt-type presence-background model": maxent_type,
}


def run_protocol(data, folds, protocol, extra=None):
    methods = dict(extra or {}, **METHODS)
    rows, seed_rows, imp_rows = [], [], []
    for k, (tr, va) in enumerate(folds):
        A, B = data.iloc[tr], data.iloc[va]
        for name, fn in methods.items():
            if name.startswith("RF + random"):
                per_seed = []
                sc, yh = fn(A, B, per_seed)
                for seed, s_ in per_seed:
                    seed_rows.append(pd.DataFrame(dict(method=name, seed=seed, fold=k, group=B.group.values,
                                                       s=B.classes.values, score=s_, yhat=s_ >= 0.5)))
            else:
                sc, yh = fn(A, B)
            rows.append(pd.DataFrame(dict(method=name, fold=k, group=B.group.values,
                                          s=B.classes.values, score=sc, yhat=yh)))
        # out-of-sample permutation importance of the PU-RF (AUC against the original labels)
        if B.classes.nunique() == 2:
            X, y = pu_training_set(A)
            m = rf().fit(X, y)
            pi = permutation_importance(m, B[FEATS], B.classes, scoring="roc_auc", n_repeats=10,
                                        random_state=0, n_jobs=-1)
            imp_rows.append(dict(protocol=protocol, fold=k, **{f"perm_{f}": v for f, v in zip(FEATS, pi.importances_mean)},
                                 **{f"gini_{f}": v for f, v in zip(FEATS, m.feature_importances_)}))
        print(f"  {protocol}: fold {k + 1}/{len(folds)}", flush=True)
    oof = pd.concat(rows)
    seeds = pd.concat(seed_rows)
    per_seed = pd.DataFrame([dict(protocol=protocol, method=m, seed=s, **metrics(x.s, x.score, x.yhat))
                             for (m, s), x in seeds.groupby(["method", "seed"])])
    summ, diffs = bootstrap(oof, protocol, REF)
    return oof.assign(protocol=protocol), summ, diffs, per_seed, pd.DataFrame(imp_rows)


# ------------------------------------------------------------------------- nested Table 2
def nested_table2(Dstar, labels, folds):
    """Table 2 metrics against the Spy labels, (i) as in the paper (labels derived once on D*)
    and (ii) nested: Spy repeated on the training folds, validation fold labeled by that NB."""
    models = {"Random Forest": rf(), "CART": DecisionTreeClassifier(random_state=42),
              "Minimum Distance": make_pipeline(StandardScaler(), NearestCentroid())}
    rows = []
    for k, (tr, va) in enumerate(folds):
        A, B = Dstar.iloc[tr], Dstar.iloc[va]
        p, u = A[A.classes == 1], A[A.classes == 0]
        X_spy, X_lab = train_test_split(p[FEATS].values, test_size=0.8, random_state=42,
                                        stratify=np.ones(len(p)))
        nb = GaussianNB().fit(np.vstack([X_lab, u[FEATS].values, X_spy]),
                              np.r_[np.ones(len(X_lab)), np.zeros(len(u) + len(X_spy))])
        tau = threshold(nb.predict_proba(X_spy)[:, 1])
        lab = lambda D: np.where(D.classes == 1, 1, (nb.predict_proba(D[FEATS].values)[:, 1] >= tau).astype(int))
        for design, ya, yb in (("paper (labels derived once on D*)", labels.loc[A.index].values, labels.loc[B.index].values),
                               ("nested (labels derived within each training fold)", lab(A), lab(B))):
            for name, tmpl in models.items():
                m = clone(tmpl).fit(A[FEATS], ya)
                yh = m.predict(B[FEATS])
                if hasattr(m, "predict_proba") and name != "Minimum Distance":
                    sc = m.predict_proba(B[FEATS])[:, 1]
                else:  # nearest centroid: distance difference as a score
                    Zb = m[:-1].transform(B[FEATS])
                    c = m[-1].centroids_
                    sc = np.linalg.norm(Zb - c[0], axis=1) - np.linalg.norm(Zb - c[1], axis=1)
                rows.append(dict(design=design, model=name, fold=k, accuracy=accuracy_score(yb, yh),
                                 precision=precision_score(yb, yh), recall=recall_score(yb, yh),
                                 f1=f1_score(yb, yh), roc_auc=roc_auc_score(yb, sc), kappa=cohen_kappa_score(yb, yh)))
    r = pd.DataFrame(rows)
    return r.groupby(["design", "model"]).agg(["mean", "std"]).drop(columns="fold")


# ------------------------------------------------------------------------- main
if __name__ == "__main__":
    d = load()
    Dstar, test, labels, folds_A, info = protocol_5fold(d)
    info["table2_rf_auc_vs_spy_labels"] = np.mean([roc_auc_score(
        labels.loc[Dstar.index[va]], rf().fit(Dstar.iloc[tr][FEATS], labels.loc[Dstar.index[tr]])
        .predict_proba(Dstar.iloc[va][FEATS])[:, 1]) for tr, va in folds_A])
    info["test_recall_342"] = (rf().fit(Dstar[FEATS], labels.loc[Dstar.index]).predict(test[FEATS])[test.classes.values == 1]).mean()
    pd.Series(info).to_csv(OUT / "00_reproduction_check.csv")
    print("reproduction check:", {k: round(float(v), 3) for k, v in info.items()})

    nested_table2(Dstar, labels, folds_A).to_csv(OUT / "07_table2_nested_vs_paper.csv")

    dl, folds_B = protocol_lso(d)
    outs = [run_protocol(Dstar, folds_A, "5-fold spatial CV", {"PU-RF (labels of the paper, derived once on D*)": pu_paper_labels(labels)}),
            run_protocol(dl, folds_B, "leave-sector-out")]
    oof, summ, diffs, per_seed, imp = (pd.concat(x) for x in zip(*outs))
    summ.to_csv(OUT / "01_metrics_summary.csv", index=False)
    diffs.to_csv(OUT / "02_paired_differences_vs_PU-RF.csv", index=False)
    per_seed.to_csv(OUT / "03_random_negatives_per_seed.csv", index=False)
    imp.to_csv(OUT / "04_importance_per_fold.csv", index=False)
    (oof[oof.protocol == "leave-sector-out"].query("s == 1").groupby(["method", "group"]).yhat.mean()
     .unstack(0).to_csv(OUT / "05_recall_per_held_out_sector.csv"))
    oof.to_csv(OUT / "06_out_of_fold_predictions.csv.gz", index=False)

    pd.set_option("display.width", 250, "display.max_colwidth", 70)
    print(summ[["protocol", "method", "auc_pu", "auc_pu_lo", "auc_pu_hi", "recall", "recall_lo", "recall_hi",
                "pred_pos_rate", "lee_liu", "recall_top10"]].round(3).to_string(index=False))
    print(diffs.round(3).to_string(index=False))
    print(imp.groupby("protocol").mean(numeric_only=True).drop(columns="fold").T.round(4))
    print(pd.read_csv(OUT / "07_table2_nested_vs_paper.csv", header=[0, 1], index_col=[0, 1]).round(3))
