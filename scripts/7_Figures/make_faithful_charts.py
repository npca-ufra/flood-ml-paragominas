"""Vector (PDF) versions of the chart figures of the submitted manuscript, drawn with the plotting code of the
original analysis (notebook 3.1: seaborn calls, colors, markers, labels) from the published data.
Each figure is drawn at the size at which it is printed (manuscript text width 4.79 in, supplement 5.15 in) so
that its text is 6.5-8 pt in print; figure-level titles are left to the caption, as the journal's artwork
guide asks. Dense scatter points are rasterized inside the PDF.
Fig. 7 (cell 25), Fig. 9 (cell 14 plus the threshold lines of the published figure), Fig. 13 (cell 26),
Figs. S1-S3 (cell 22); Fig. 14 reproduces the published bar chart, and Fig. 19 the Google Earth Engine
histogram chart of script 5.1 (FSIVI raster of Zenodo 10.5281/zenodo.21227777, bucket width 0.0039)."""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib._mathtext as mathtext
mathtext.SHRINK_FACTOR = 0.8  # sub/superscripts at 80% (default 70%) so that they stay >= 6 pt in print
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd
import seaborn as sns

HERE = Path(__file__).resolve().parent
OUT = HERE / "output"; OUT.mkdir(exist_ok=True)
sys.path.insert(0, str(HERE.parent / "6_RevisionAnalyses"))
from common import DATA, FEATS, load, protocol_5fold, spy_scores  # noqa: E402

TW, TWS = 4.79, 5.15  # printed text widths (in) of the manuscript and of the supplement
plt.rcParams.update({"pdf.fonttype": 42, "mathtext.fontset": "custom", "mathtext.rm": "Arial", "mathtext.it": "Arial:italic", "mathtext.bf": "Arial:bold"})
# Arial, as asked by the journal (seaborn's default; the original Colab run fell back to DejaVu Sans on Linux)
RC = {"font.sans-serif": ["Arial"], "font.size": 7.5, "axes.labelsize": 7.5, "axes.titlesize": 7.5,
      "xtick.labelsize": 7, "ytick.labelsize": 7, "legend.fontsize": 7, "legend.title_fontsize": 7.5,
      "axes.linewidth": 0.6, "grid.linewidth": 0.5, "lines.linewidth": 1.0, "patch.linewidth": 0.6,
      "xtick.major.width": 0.6, "ytick.major.width": 0.6}
sns.set_style("whitegrid", RC); plt.rcParams.update(RC)
d = load()
Dstar, test, labels, folds, info = protocol_5fold(d)

# Fig. 7 - spatial distribution of the held-out test samples (cell 25), printed at the text width
t = test.assign(sample_type=test.classes.map({1: "Flood samples", 0: "Unlabeled samples"}))
plt.figure(figsize=(TW, 3.55))
sns.scatterplot(data=t, x="lon", y="lat", hue="sample_type", hue_order=["Unlabeled samples", "Flood samples"],
                palette={"Flood samples": "red", "Unlabeled samples": "blue"}, style="sample_type",
                style_order=["Unlabeled samples", "Flood samples"],
                markers={"Flood samples": "X", "Unlabeled samples": "o"}, s=7, alpha=0.8, linewidth=0.2,
                rasterized=True)
plt.xlabel("Longitude"); plt.ylabel("Latitude")
plt.gca().xaxis.set_major_locator(mticker.MultipleLocator(0.01))   # as published; 0.005 steps overlap in print
plt.legend(title="Sample Type", loc="upper left", markerscale=0.8)   # inside the plot, over the empty corner
plt.grid(True); plt.tight_layout()
plt.savefig(OUT / "Fig7.pdf", dpi=600); plt.close()

# Fig. 9 - spy probabilities (cell 14) with the two threshold lines of the published figure
pos, unl = Dstar[Dstar.classes == 1], Dstar[Dstar.classes == 0]
proba_positive, _ = spy_scores(pos[FEATS].values, unl[FEATS].values)
mu_sigma, q1 = proba_positive.mean() - proba_positive.std(), np.percentile(proba_positive, 25)
plt.figure(figsize=(0.85 * TW, 2.45))
ax = sns.histplot(proba_positive, bins=50, kde=True, line_kws={"linewidth": 1.0})
top = ax.get_ylim()[1]
ax.axvline(mu_sigma, ls="--", lw=0.8, color="#c55a11")
ax.text(mu_sigma - 0.006, top * 0.97, "μ−σ = %.2f" % mu_sigma, color="#c55a11", fontsize=7.5, va="top", ha="right")
ax.axvline(q1, ls="--", lw=0.8, color="#b22234")
ax.text(q1 + 0.006, top * 0.89, r"$Q_1$ = %.2f" % q1, color="#b22234", fontsize=7.5, va="top")  # 7.5 pt: subscript 6 pt
plt.xlabel("Probability"); plt.ylabel("Frequency")
plt.grid(True); plt.tight_layout()
plt.savefig(OUT / "Fig9.pdf"); plt.close()

# Fig. 13 - aggregated confusion matrices of the original run, counts as published (cell 26)
CM = {"Random Forest": [[8735, 320], [536, 5246]], "CART": [[8282, 773], [714, 5068]],
      "Minimum Distance": [[6662, 2393], [198, 5584]]}
fig_cm, axes_cm = plt.subplots(1, 3, figsize=(TW, 1.85))
for k, (a, (model_name, cm)) in enumerate(zip(axes_cm, CM.items())):
    sns.heatmap(np.array(cm), annot=np.vectorize("{:,}".format)(np.array(cm)), fmt="", cmap="Blues", cbar=False, annot_kws={"fontsize": 7.5},
                xticklabels=[0, 1], yticklabels=[0, 1], ax=a, linewidths=0)
    a.set_xlabel("Predicted Classes"); a.set_ylabel("True Classes" if a is axes_cm[0] else "")   # shared y label
    a.set_title(f"({'ABC'[k]}) {model_name}")
plt.tight_layout(w_pad=0.6)
plt.savefig(OUT / "Fig13.pdf"); plt.close()

# Fig. 14 - normalized FSIVI weights (published bar chart)
sns.set_style("white", RC)
imp = pd.read_csv(DATA / "feature_importance_flood.csv")[FEATS].iloc[0]
w = (imp / imp.sum()).sort_values()
names = {"ksat": r"$k_{sat}$", "slope": "Slope", "distance": "Distance", "elevation": "Elevation", "hand": "HAND", "twi": "TWI"}
fig, ax = plt.subplots(figsize=(0.76 * TW, 2.1))
ax.barh([names[k] for k in w.index], w.values, color="#3a6ea5", edgecolor="black", linewidth=0.5, height=0.8)
for i, k in enumerate(w.index):
    ax.text(w[k] + 0.006, i, r"$w$=%.2f  ($I$=%.1f)" % (w[k], imp[k]), va="center", fontsize=6.5)
ax.set_xlim(0, 0.32); ax.set_xticks(np.arange(0, 0.31, 0.05))
ax.xaxis.grid(True, ls=":", color="#bbbbbb", lw=0.5); ax.set_axisbelow(True)
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
ax.tick_params(axis="y", length=2.5, left=True, labelsize=7.5); ax.tick_params(axis="x", length=2.5, bottom=True)
ax.set_xlabel(r"Normalized FSIVI weight $w_i$")
fig.tight_layout(); fig.savefig(OUT / "Fig14.pdf"); plt.close(fig)

# Fig. 19 - FSIVI histogram (Google Earth Engine ui.Chart.image.histogram of script 5.1)
x = np.load(HERE / "inputs" / "fsivi_values_domain.npy")
wb, off = 0.0039, 0.00078
edges = np.arange(0.2 - off, 1.0, wb)
h, _ = np.histogram(x, edges)
with plt.rc_context({"font.family": "Arial"}):
    fig, ax = plt.subplots(figsize=(0.85 * TW, 1.8))
    ax.bar(edges[:-1] + wb / 2, h, width=wb * 0.72, color="purple", linewidth=0)
    ax.set_xlim(0.228, 0.95); ax.set_ylim(0, 2000)
    ax.set_xticks(np.arange(0.3, 0.91, 0.1)); ax.set_yticks(np.arange(0, 2001, 500))
    ax.set_xticks(np.arange(0.25, 0.96, 0.1), minor=True)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:,.0f}"))
    ax.grid(True, color="#d6d6d6", lw=0.5); ax.grid(True, which="minor", axis="x", color="#eeeeee", lw=0.5)
    ax.set_axisbelow(True); ax.axhline(0, color="#333333", lw=0.6)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.tick_params(which="both", length=0, labelsize=7, labelcolor="#444444")
    ax.set_xlabel("FSIVI value", fontsize=7.5, style="italic", color="#444444")
    ax.set_ylabel("Frequency", fontsize=7.5, style="italic", color="#444444")
    fig.tight_layout(); fig.savefig(OUT / "Fig19.pdf"); plt.close(fig)

# Figs. S1-S3 - predictors of D* by new class (cell 22), printed at the supplement text width
sns.set_style("whitegrid", RC)
# readable labels instead of the notebook's column names (the journal asks that symbols be explained)
long = {"ksat": r"$k_{sat}$ (cm/d)", "slope": "Slope (°)", "distance": "Distance (m)", "elevation": "Elevation (m)",
        "hand": "HAND (m)", "twi": "TWI"}
df = Dstar[FEATS].rename(columns=long).assign(Class=labels.loc[Dstar.index].values.astype(int))

plt.figure(figsize=(TWS, 3.9))
for i, col in enumerate(df.columns[:-1]):
    plt.subplot(2, 3, i + 1)
    sns.boxplot(x="Class", y=col, data=df, linewidth=0.6, fliersize=1.5, flierprops={"rasterized": True})
plt.tight_layout(h_pad=0.8, w_pad=0.6)
plt.savefig(OUT / "FigS1.pdf", dpi=600); plt.close()

corr = Dstar[FEATS].rename(columns={k: v.split(" (")[0] for k, v in long.items()}).corr(method="pearson")
plt.figure(figsize=(0.8 * TWS, 3.1))
sns.heatmap(corr, annot=True, cmap="coolwarm", fmt=".2f", annot_kws={"fontsize": 7})
plt.xticks(rotation=90, fontsize=7.5); plt.yticks(rotation=0, fontsize=7.5)   # 7.5 pt: subscript of k_sat at 6 pt
plt.tight_layout()
plt.savefig(OUT / "FigS2.pdf", dpi=600); plt.close()   # dpi applies to the rasterized color bar

with sns.plotting_context(rc={"font.size": 6.2, "axes.labelsize": 7.5, "xtick.labelsize": 6, "ytick.labelsize": 6,
                              "legend.fontsize": 6.2, "legend.title_fontsize": 6.2}):
    g = sns.pairplot(df, hue="Class", diag_kind="kde", height=TWS / 6.6,
                     plot_kws={"rasterized": True, "s": 2.5, "linewidth": 0.1}, diag_kws={"linewidth": 0.6})
    for a in g.axes.flat:
        if a is not None:
            a.tick_params(length=1.5, pad=1)
    plt.savefig(OUT / "FigS3.pdf", dpi=600, bbox_inches="tight", pad_inches=0.02); plt.close()
print("ok", round(mu_sigma, 3), round(q1, 3), len(test), x.size, h.max())
