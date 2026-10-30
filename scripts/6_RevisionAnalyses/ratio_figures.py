"""Figures for the map-level effect of the positive-to-negative ratio (results of map_level.py and
ratio_lso.py): (a) summary curves; (b) maps of the PU model and of random-negative models."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib._mathtext as mathtext
mathtext.SHRINK_FACTOR = 0.8  # sub/superscripts at 80% (default 70%) so that they stay >= 6 pt in print
import numpy as np
import pandas as pd

import map_level as ml
from common import FEATS, results_dir, rf

OUT = results_dir("results")
FIG = results_dir("figures")
plt.rcParams.update({"font.family": "Arial", "mathtext.fontset": "custom", "mathtext.rm": "Arial", "mathtext.it": "Arial:italic", "mathtext.bf": "Arial:bold", "font.size": 8, "pdf.fonttype": 42, "axes.spines.top": False, "axes.spines.right": False})

raw = pd.read_csv(OUT / "15_map_level_metrics.csv").groupby("model", sort=False)
mp, lo, hi = raw.mean(numeric_only=True), raw.min(numeric_only=True), raw.max(numeric_only=True)
lso = pd.read_csv(OUT / "17_ratio_leave_sector_out.csv").set_index("model")
pu_lso = pd.read_csv(OUT / "01_metrics_summary.csv").query("protocol == 'leave-sector-out' and method == 'PU-RF'").iloc[0]
labels = ["1:0.5", "1:1", "1:2", "1:4.7", "1:6.7\n(all)"]
keys = ["1:0.5", "1:1", "1:2", "1:4.7 (PU count)", "all unlabeled (1:6.7)"]
x = np.arange(len(keys))
col = lambda df, c: np.array([df.loc[f"RF + random negatives {k}", c] for k in keys])
area, fpb = col(mp, "predicted_ha"), col(mp, "Fpb")
err = lambda c: [col(mp, c) - col(lo, c), col(hi, c) - col(mp, c)]  # range across the ten draws
rec = [lso.loc[k, "recall"] for k in keys]
ll = [lso.loc[k, "lee_liu"] for k in keys]
pu = mp.loc["PU-RF (paper labels)"]
seeds = pd.read_csv(OUT / "18_pu_map_stability.csv")  # PU maps across spy seeds

# printed size (manuscript text width 4.79 in), so 8 pt here is 8 pt in print
fig, ax = plt.subplots(2, 2, figsize=(4.79, 4.1), sharex=True)
RN, PU = dict(fmt="o-", c="#c0392b", ms=3.5, capsize=2, lw=1.2), dict(c="#1f5f99", ls="--", lw=1.2)
# PU band: range across spy seeds (A, B); 95% sector-bootstrap interval of Table 5 (C, D)
panels = [("(A) Mapped extent", "Area mapped (ha)", area, err("predicted_ha"), pu.predicted_ha, (seeds.predicted_ha.min(), seeds.predicted_ha.max())),
          ("(B) In-sample agreement", "$F_{pb}$ against the sectors", fpb, err("Fpb"), pu.Fpb, (seeds.Fpb.min(), seeds.Fpb.max())),
          ("(C) Withheld sectors", "Recall (leave-sector-out)", rec, None, pu_lso.recall, (pu_lso.recall_lo, pu_lso.recall_hi)),
          ("(D) Withheld sectors", "Lee–Liu (leave-sector-out)", ll, None, pu_lso.lee_liu, (pu_lso.lee_liu_lo, pu_lso.lee_liu_hi))]
for a, (title, ylab, yv, ye, ref, band) in zip(ax.flat, panels):
    a.axhspan(*band, color="#1f5f99", alpha=0.15, lw=0)
    a.errorbar(x, yv, ye, **RN, label="Random pseudo-negatives"); a.axhline(ref, **PU, label="PU labels")
    a.set_title(title, loc="left"); a.set_ylabel(ylab)
for a in ax[1]:
    a.set_xticks(x); a.set_xticklabels(labels); a.set_xlabel("Positives : negatives")
ax[1, 0].set_ylim(0, 0.85); ax[1, 1].set_ylim(0, 1.75)
h, l = ax[0, 0].get_legend_handles_labels()
fig.legend(h[::-1], l[::-1], loc="lower center", ncol=2, frameon=False)
fig.tight_layout(rect=(0, 0.05, 1, 1), h_pad=0.6); fig.savefig(FIG / "ratio_effect_summary.png", dpi=300); fig.savefig(FIG / "ratio_effect_summary.pdf"); plt.close(fig)

# maps
pos, unl = ml.Dstar[ml.Dstar.classes == 1], ml.Dstar[ml.Dstar.classes == 0]
panels = [("PU labels", ml.predict(rf().fit(ml.Dstar[FEATS], ml.labels.loc[ml.Dstar.index])))]
for name, k in [("Random negatives 1:0.5", 0.5), ("Random negatives 1:1", 1), ("All unlabeled as negatives", None)]:
    neg = unl if k is None else unl.sample(int(round(k * len(pos))), random_state=0)
    m = ml.predict(rf(0).fit(pd.concat([pos[FEATS], neg[FEATS]]), np.r_[np.ones(len(pos)), np.zeros(len(neg))]))
    panels.append((name, m))
anym = ml.ref.copy()
for _, m in panels:
    anym |= m
rows, cols = np.where(anym)
pad = 25
r0, r1, c0, c1 = max(rows.min() - pad, 0), rows.max() + pad, max(cols.min() - pad, 0), cols.max() + pad
fig, ax = plt.subplots(2, 2, figsize=(5.15, 5.9))
for a, (name, m) in zip(ax.flat, panels):
    img = np.ones(ml.shape + (3,))
    img[ml.urban] = (0.86, 0.86, 0.86)
    img[m] = (0.84, 0.15, 0.15)
    img[ml.ref & ~m] = (0.15, 0.35, 0.85)
    img[ml.ref & m] = (0.45, 0.05, 0.45)
    a.imshow(img[r0:r1, c0:c1], interpolation="nearest")
    ha = ml.px_ha[m].sum()
    if a is ax[0, 0]:  # 1 km scale bar and north arrow
        px_m = abs(ml.T.a) * 111320 * np.cos(np.radians(ml.T.f))
        y0 = r1 - r0 - 15
        a.plot([10, 10 + 1000 / px_m], [y0, y0], c="k", lw=2); a.text(10 + 500 / px_m, y0 - 8, "1 km", ha="center", fontsize=7.5)
        a.annotate("N", xy=(25, 15), xytext=(25, 60), ha="center", fontsize=8, arrowprops=dict(arrowstyle="-|>", color="k"))
    a.set_title(f"{name}\n{ha:.0f} ha mapped" + ("" if name.startswith(("PU", "All")) else " (draw 1 of 10)"), fontsize=10); a.axis("off")
from matplotlib.patches import Patch
fig.legend(handles=[Patch(color=(0.84, 0.15, 0.15), label="Mapped, outside CPRM/SGB sectors"), Patch(color=(0.45, 0.05, 0.45), label="Mapped, inside CPRM/SGB sectors"),
                    Patch(color=(0.15, 0.35, 0.85), label="Sector not mapped"), Patch(color=(0.86, 0.86, 0.86), label="Urban area")],
           loc="lower center", ncol=2, frameon=False, fontsize=8)
fig.tight_layout(rect=(0, 0.07, 1, 1)); fig.savefig(FIG / "ratio_effect_maps.png", dpi=300)
fig.savefig(FIG / "ratio_effect_maps.pdf", dpi=600); plt.close(fig)  # vector text, maps resampled at 600 dpi
print("ok")
