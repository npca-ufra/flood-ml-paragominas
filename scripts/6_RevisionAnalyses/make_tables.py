"""Builds the LaTeX rows of the benchmark tables (main-text Table 5 and Table S3) from results/."""
import pandas as pd

from common import DATA

s = pd.read_csv("results/01_metrics_summary.csv")
eq = pd.read_csv("results/11_equal_predicted_area.csv").set_index(["protocol", "method"])
rs = pd.read_csv("results/05_recall_per_held_out_sector.csv", index_col=0)
lt50 = (rs < 0.5).sum()
MAIN = {"PU-RF": "PU-RF (proposed)",
        "RF + random negatives (1:1)": "RF + random negatives (1:1)",
        "RF + random negatives (same number as PU reliable negatives)": "RF + random negatives (PU count)",
        "Elkan-Noto (RF)": "Elkan--Noto (RF)", "PU bagging (RF)": "PU bagging (RF)",
        "One-class SVM": "One-class SVM", "MaxEnt-type presence-background model": "MaxEnt-type model",
        "PU-XGBoost": "PU-XGBoost", "PU-SVM (RBF)": "PU-SVM (RBF)"}
FULL = {"PU-RF (labels of the paper, derived once on D*)": "PU-RF, labels of the paper (derived once on $D^{*}$)",
        "PU-RF": "PU-RF (Spy within training folds)",
        **{k: v for k, v in MAIN.items() if k != "PU-RF"},
        "PU-RF, mu-sigma threshold (no fallback)": "PU-RF, $\\mu_{spy}-\\sigma_{spy}$ threshold",
        "PU-RF, 10th-percentile threshold": "PU-RF, 10th-percentile threshold",
        "PU-RF without ksat": "PU-RF without $k_{sat}$"}
TITLE = {"5-fold spatial CV": "5-fold spatial cross-validation (Spectral Clustering groups, $D^{*}$)",
         "leave-sector-out": "Leave-sector-out (18 sectors, full sample set)"}


def ci(r, k, f="{:.2f}"):
    return f"{f.format(r[k])} ({r[k + '_lo']:.2f}--{r[k + '_hi']:.2f})"


L = s[s.protocol == "leave-sector-out"].set_index("method")
def eqcols(prot, k):
    e = eq.loc[(prot, k)]
    return f"{e.lee_liu_equal_share:.2f} & {e.max_lee_liu:.2f}"


main = [f"{v} & {ci(L.loc[k], 'auc_pu', '{:.3f}')} & {ci(L.loc[k], 'recall')} & {L.loc[k].pred_pos_rate:.2f} & "
        f"{ci(L.loc[k], 'lee_liu')} & {eqcols('leave-sector-out', k)} & {L.loc[k].recall_top10:.2f} & {lt50[k]} \\\\" for k, v in MAIN.items()]
full = []
for prot, title in TITLE.items():
    P = s[s.protocol == prot].set_index("method")
    full.append("\\multicolumn{8}{l}{\\textit{" + title + "}}\\\\")
    full += [f"{v} & {ci(P.loc[k], 'auc_pu', '{:.3f}')} & {ci(P.loc[k], 'recall')} & {P.loc[k].pred_pos_rate:.2f} & "
             f"{ci(P.loc[k], 'lee_liu')} & {eqcols(prot, k)} & {ci(P.loc[k], 'recall_top10')} \\\\" for k, v in FULL.items() if k in P.index]
open("results/table_benchmark_main.tex", "w").write("\n".join(main) + "\n")
open("results/table_S3.tex", "w").write("\n".join(full) + "\n")
print("\n".join(main))

# Table S4: Table 2 metrics, paper design vs nested design (offline reproduction)
n = pd.read_csv("results/07_table2_nested_vs_paper.csv", header=[0, 1], index_col=[0, 1])
s4 = []
for design, title in [("paper (labels derived once on D*)", "Labels derived once on $D^{*}$ (design of Table~2)"),
                      ("nested (labels derived within each training fold)", "Nested: labels derived within each training fold")]:
    s4.append("\\multicolumn{7}{l}{\\textit{" + title + "}}\\\\")
    for model in ["Random Forest", "CART", "Minimum Distance"]:
        r = n.loc[(design, model)]
        s4.append(model + " & " + " & ".join(f"{r[(m, 'mean')]:.3f} ({r[(m, 'std')]:.3f})"
                                              for m in ["accuracy", "precision", "recall", "f1", "roc_auc", "kappa"]) + " \\\\")
open("results/table_S4.tex", "w").write("\n".join(s4) + "\n")

# Table S5: importance (mean over folds); Gini of this reproduction and GEE weights of Table 3
imp = pd.read_csv("results/04_importance_per_fold.csv").groupby("protocol").mean(numeric_only=True)
gee = pd.read_csv(DATA / "feature_importance_flood.csv")[["ksat", "slope", "distance", "elevation", "hand", "twi"]].iloc[0]
gee = gee / gee.sum()
lab = {"ksat": "$k_{sat}$", "slope": "Slope", "distance": "Distance to drainage", "elevation": "Elevation", "hand": "HAND", "twi": "TWI"}
s5 = [f"{lab[f]} & {gee[f]:.3f} & {imp.loc['5-fold spatial CV', 'gini_' + f]:.3f} & {imp.loc['leave-sector-out', 'gini_' + f]:.3f} & "
      f"{imp.loc['5-fold spatial CV', 'perm_' + f]:.3f} & {imp.loc['leave-sector-out', 'perm_' + f]:.3f} \\\\" for f in lab]
open("results/table_S5.tex", "w").write("\n".join(s5) + "\n")
print("\n".join(s4)); print("\n".join(s5))

# Table S6: map-level effect of the ratio of random pseudo-negatives (map_level.py, ratio_lso.py, pu_map_stability.py)
mp = pd.read_csv("results/15_map_level_metrics.csv")
st = pd.read_csv("results/18_pu_map_stability.csv").assign(model="PU spy seeds")
ag = pd.read_csv("results/16_map_level_agreement.csv").set_index("model")
rl = pd.read_csv("results/17_ratio_leave_sector_out.csv").set_index("model")
pu_l = L.loc["PU-RF"]
rng = lambda x, c, f: f"{x[c].mean():{f}}" + (f" ({x[c].min():{f}}--{x[c].max():{f}})" if len(x) > 1 else "")
def row6(label, x, jb, jp, lso):
    return (f"{label} & {rng(x, 'predicted_ha', '.1f')} & {rng(x, 'area_recall', '.3f')} & {rng(x, 'area_precision', '.3f')} & "
            f"{rng(x, 'Fpb', '.2f')} & {jb} & {jp} & {lso} \\\\")
lso = lambda r: f"{r.auc_pu:.3f} & {r.recall:.2f} & {r.lee_liu:.2f}"
s6 = [row6("PU labels", mp[mp.model == "PU-RF (paper labels)"], "--", "1", lso(pu_l)),
      row6("PU labels, ten spy seeds", st, f"{st.jaccard_between_seeds_mean.iloc[0]:.2f}", "--", "-- & -- & --")]
for k, lab6 in [("1:0.5", "1:0.5"), ("1:1", "1:1"), ("1:2", "1:2"), ("1:4.7 (PU count)", "1:4.7 (PU count)"), ("all unlabeled (1:6.7)", "all unlabeled (1:6.7)")]:
    jb = ag.loc[k, "jaccard_between_draws_mean"]
    s6.append(row6("Random negatives " + lab6, mp[mp.model == f"RF + random negatives {k}"],
                   "--" if pd.isna(jb) else f"{jb:.2f}", f"{ag.loc[k, 'jaccard_with_PU_mean']:.2f}", lso(rl.loc[k])))
open("results/table_S6.tex", "w").write("\n".join(s6) + "\n")
print("\n".join(s6))
