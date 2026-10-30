"""Figs. 11 and 12 of the submitted manuscript come from the original Colab run (spatial folds and per-fold ROC
curves), which the offline reproduction does not recreate exactly. Their plotting areas are therefore kept as
the original pixels and only the lettering (ticks, axis labels, legends) is redrawn as vector text at print size.

Fig. 11: the higher-resolution export of the same plot as `inputs/Fig11_original_run.png` (a higher-resolution export of the same plot) (4200 x 3600 px, same
folds and counts) assigns the tab10 colors in lexicographic fold order (1, 10, 2, ...), while the submitted
figure assigns them in numeric order; its points are recolored to the submitted colors before use.
Fig. 12: the submitted PNG (5400 x 1800 px); the legend boxes, drawn inside the plotting areas, are replaced by
vector legends below each panel."""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.legend_handler import HandlerTuple
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from PIL import Image
from matplotlib import patheffects
from scipy import ndimage

HERE = Path(__file__).resolve().parent
OUT = HERE / "output"; OUT.mkdir(exist_ok=True)
INPUTS = HERE / "inputs"                  # images of the submitted manuscript
SUBM = INPUTS
TW = 4.79
RC = {"font.family": "Arial", "mathtext.fontset": "custom", "mathtext.rm": "Arial", "mathtext.it": "Arial:italic", "mathtext.bf": "Arial:bold", "font.size": 7, "axes.labelsize": 7, "axes.titlesize": 7, "xtick.labelsize": 6.5,
      "ytick.labelsize": 6.5, "legend.fontsize": 6.5, "legend.title_fontsize": 7, "pdf.fonttype": 42,
      "axes.edgecolor": "#cccccc", "axes.linewidth": 0.6, "xtick.color": "#262626", "ytick.color": "#262626",
      "xtick.major.size": 0, "ytick.major.size": 0}
plt.rcParams.update(RC)
TAB10 = np.array([[31, 119, 180], [255, 127, 14], [44, 160, 44], [214, 39, 40], [148, 103, 189], [140, 86, 75],
                  [227, 119, 194], [127, 127, 127], [188, 189, 34], [23, 190, 207]], float)


def calib(px, ticks):
    """Linear map pixel -> data from gridline pixel centres and their tick values."""
    a, b = np.polyfit(px, ticks, 1)
    return lambda p: a * p + b


# ---------------- Fig. 11 ----------------
img = np.array(Image.open(INPUTS / "Fig11_original_run.png").convert("RGB")).astype(float)
x0, x1, y0, y1 = 263, 3173, 115, 3423                         # inside the axes spines
gx = [377, 721, 1065, 1409, 1752, 2096, 2440, 2783, 3127]     # gridline centres (px), lon -47.380 ... -47.340
gy = [376, 1090, 1804, 2518, 3232]                            # lat -2.97 ... -3.01
lon, lat = calib(gx, np.arange(-47.380, -47.3399, 0.005)), calib(gy, [-2.97, -2.98, -2.99, -3.00, -3.01])
sub = img[y0:y1, x0:x1]
# canonical palette index of each fold, by lexicographic order of the labels: 1, 10, 2, 3, ..., 9
canon_of_fold = {1: 0, 10: 1, 2: 2, 3: 3, 4: 4, 5: 5, 6: 6, 7: 7, 8: 8, 9: 9}
subm_of_fold = {k: k - 1 for k in range(1, 11)}               # submitted: fold k -> tab10 colour k-1
white = np.array([255.0, 255.0, 255.0])
src = TAB10[[canon_of_fold[k] for k in range(1, 11)]]
dst = TAB10[[subm_of_fold[k] for k in range(1, 11)]]
flat = sub.reshape(-1, 3)
d = flat[:, None, :] - white                                   # pixel = white + alpha * (colour - white)
v = src[None] - white
alpha = np.clip((d * v).sum(-1) / (v * v).sum(-1), 0, 1)
resid = np.linalg.norm(d - alpha[..., None] * v, axis=-1)
k = resid.argmin(1)
ak, rk = alpha[np.arange(len(k)), k], resid[np.arange(len(k)), k]
# keep white, the light grid lines and pixels that match no fold colour
# grid lines: darker in this export (core 176) than in the submitted figure (#cccccc), so they are re-toned
gridmask = np.zeros(sub.shape[:2], bool)
for g in gx:
    gridmask[:, g - x0 - 4:g - x0 + 5] = True
for g in gy:
    gridmask[g - y0 - 4:g - y0 + 5, :] = True
neutral = np.ptp(flat, 1) < 10
on_grid = neutral & gridmask.ravel() & (flat.min(1) >= 150)
recolor = (ak > 0.04) & (rk < 40) & ~on_grid & ~(neutral & (flat.min(1) > 200))
out = flat.copy()
out[recolor] = white + ak[recolor, None] * (dst[k[recolor]] - white)
out[on_grid] = 255 - (255 - flat[on_grid]) * (255 - 204) / (255 - 176)
sub_new = out.reshape(sub.shape).clip(0, 255).astype(np.uint8)
print("Fig. 11: recolored pixels", recolor.mean().round(3))

# plotting area keeps the pixel aspect of the original (3308 / 2910)
fig = plt.figure(figsize=(TW, 3.55))
ax = fig.add_axes([0.098, 0.105, 2.64 / TW, 3.0 / 3.55])
ext = (lon(x0 - 0.5), lon(x1 - 0.5), lat(y1 - 0.5), lat(y0 - 0.5))
ax.imshow(sub_new, extent=ext, interpolation="lanczos", aspect="auto")
ax.set_xlim(ext[0], ext[1]); ax.set_ylim(ext[2], ext[3])
ax.set_xticks(np.arange(-47.380, -47.3399, 0.005))
ax.set_xticklabels([f"{t:.3f}".replace("-", "−") if i % 2 == 0 else "" for i, t in enumerate(np.arange(-47.380, -47.3399, 0.005))])
ax.set_yticks([-2.97, -2.98, -2.99, -3.00, -3.01]); ax.set_yticklabels([f"{t:.2f}".replace("-", "−") for t in [-2.97, -2.98, -2.99, -3.00, -3.01]])
ax.set_xlabel("Longitude"); ax.set_ylabel("Latitude")
# group numbers written on the map, so that groups do not depend on color alone (color-blind readers)
fold = np.zeros(recolor.shape, int)
fold[recolor] = k[recolor] + 1                               # src order is fold 1 ... 10
fold = fold.reshape(sub.shape[:2])
for f in range(1, 11):
    blobs, n = ndimage.label(ndimage.binary_closing(fold == f, iterations=6))
    for b in range(1, n + 1):
        cy, cx = ndimage.center_of_mass(blobs == b)
        if (blobs == b).sum() > 20000:                       # whole clusters, not stray pixels
            ax.text(lon(x0 + cx), lat(y0 + cy), str(f), ha="center", va="center", fontsize=7, weight="bold",
                    path_effects=[patheffects.withStroke(linewidth=1.8, foreground="white")])
counts = {1: 2726, 2: 976, 3: 1434, 4: 1040, 5: 2041, 6: 1002, 7: 1597, 8: 1306, 9: 1292, 10: 1423}
mk = {1: (4, 0, 45), 2: "P", 3: (4, 0, 0), 4: (4, 1, 0), 5: "X", 6: (6, 1, 0), 7: (4, 1, 45), 8: "^", 9: "v", 10: "o"}
handles = [Line2D([], [], ls="", marker=mk[f], markersize=4.5, markerfacecolor=TAB10[f - 1] / 255, alpha=0.8,
                  markeredgecolor="white", markeredgewidth=0.3, label=f"Group {f} ({counts[f]:,} samples)")
           for f in range(1, 11)]
fig.legend(handles=handles, title="Spectral Clustering group", loc="upper left", bbox_to_anchor=(0.665, 0.955), frameon=True,
           edgecolor="#cccccc", handletextpad=0.3, borderpad=0.4, labelspacing=0.42, fontsize=6.6, title_fontsize=7)
fig.savefig(OUT / "Fig11.pdf", dpi=900, bbox_inches="tight", pad_inches=0.03); plt.close(fig)

# ---------------- Fig. 12 ----------------
img = np.array(Image.open(SUBM / "Fig12.png").convert("RGB"))
PANEL_X0 = [200, 1985, 3770]            # first column inside the left spine of each panel
PX = 1585                               # panel interior width (px); axes limits -0.05 ... 1.05 in both directions
Y0, Y1 = 113, 1625                      # interior rows
models = ["Random Forest", "CART", "Minimum Distance"]
aucs = {"Random Forest": ([0.97, 0.96, 0.96, 0.98, 0.99], "0.97 ± 0.01"),
        "CART": ([0.90, 0.90, 0.88, 0.92, 0.87], "0.90 ± 0.02"),
        "Minimum Distance": ([0.94, 0.96, 0.93, 0.98, 0.97], "0.96 ± 0.02")}
fig = plt.figure(figsize=(TW, 3.05))
for i, (x0, model) in enumerate(zip(PANEL_X0, models)):
    panel = img[Y0:Y1, x0:x0 + PX].copy()
    # remove the legend box (it covers only grid lines) and restore the grid lines it hid
    lx0, lx1, ly0, ly1 = 954 - 200, 1767 - 200, 1084 - Y0, 1609 - Y0
    vprof = img[600, x0 + 935 - 5:x0 + 935 + 6].copy()            # profile across the x = 0.6 grid line
    hprof = img[1281 - 5:1281 + 6, x0 + 500].copy()               # profile across the y = 0.2 grid line
    panel[ly0:ly1, lx0:lx1] = 255
    for gx_ in (935, 1224, 1512):                                 # x = 0.6, 0.8, 1.0 (px inside the panel)
        seg = panel[ly0:ly1, gx_ - 5:gx_ + 6]
        panel[ly0:ly1, gx_ - 5:gx_ + 6] = np.minimum(seg, vprof[None])
    for gy_ in (1281 - Y0, 1556 - Y0):                            # y = 0.2, 0.0
        seg = panel[gy_ - 5:gy_ + 6, lx0:lx1]
        panel[gy_ - 5:gy_ + 6, lx0:lx1] = np.minimum(seg, hprof[:, None])
    ax = fig.add_axes([0.075 + i * 0.325, 0.47, 0.24, 0.43])
    ax.imshow(panel, extent=(-0.05, 1.05, -0.05, 1.05), interpolation="lanczos", aspect="auto")
    ax.set_xlim(-0.05, 1.05); ax.set_ylim(-0.05, 1.05)
    ax.set_xticks(np.arange(0, 1.01, 0.2)); ax.set_yticks(np.arange(0, 1.01, 0.2))
    ax.tick_params(labelsize=6.4)
    ax.set_title(f"({'ABC'[i]}) {model}", fontsize=6.5)
    ax.set_xlabel("False Positive Rate", fontsize=6.5); ax.set_ylabel("True Positive Rate", fontsize=6.5)
    folds_, mean_ = aucs[model]
    # the five fold curves overlap and their tab10 colours are not separable by colour-blind readers, so they share
    # one legend entry; the fold AUCs are listed in fold order
    h = [tuple(Line2D([], [], color=f"C{j}", lw=0.8, alpha=0.6) for j in range(5))]
    lab = ["ROC of folds 1–5 (AUC =\n" + ", ".join(f"{v:.2f}" for v in folds_) + ")"]
    h += [Line2D([], [], color="r", lw=1.2, ls="--", alpha=0.8, label="Chance"),
          Line2D([], [], color="b", lw=1.2, alpha=0.8, label=f"Mean ROC (AUC = {mean_})"),
          Patch(facecolor="grey", alpha=0.2, label=r"$\pm$ 1 std. dev.")]
    lab += [x.get_label() for x in h[1:]]
    fig.legend(handles=h, labels=lab, handler_map={tuple: HandlerTuple(ndivide=None, pad=0)}, loc="upper center", bbox_to_anchor=(0.075 + i * 0.325 + 0.12, 0.335), fontsize=6.3,
               frameon=True, edgecolor="#cccccc", handlelength=1.5, handletextpad=0.3, borderpad=0.3, labelspacing=0.3)
fig.savefig(OUT / "Fig12.pdf", dpi=1200, bbox_inches="tight", pad_inches=0.03); plt.close(fig)
print("Fig. 12 done")
