"""Map figures of the submitted manuscript exported from QGIS with lettering too small for print (2-4 pt).
The map pixels are kept as published; colour bars are rebuilt from the colours sampled along the published
bars, and all text (legends, bar labels, values, panel letters) is redrawn as vector text at 6-7 pt."""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import rasterio
from PIL import Image
from scipy import ndimage
from scipy.ndimage import binary_dilation

HERE = Path(__file__).resolve().parent
OUT = HERE / "output"; OUT.mkdir(exist_ok=True)
SUBM = HERE / "inputs"                       # images of the submitted manuscript
SUBS = SUBM
DATA = HERE.parent / "files"                  # heat_map_flood_risk_postClassif.tif from Zenodo
TW = 4.79
plt.rcParams.update({"font.family": "Arial", "mathtext.fontset": "custom", "mathtext.rm": "Arial", "mathtext.it": "Arial:italic", "mathtext.bf": "Arial:bold", "font.size": 6.5, "pdf.fonttype": 42})


def load(p):
    return np.asarray(Image.open(p).convert("RGB"))


def bar_colours(img, x0, x1, y0, y1):
    """Colours along the centre column of a published colour bar, top to bottom, without its white margin."""
    col = img[y0:y1, (x0 + x1) // 2].astype(int)
    ink = np.where(np.abs(col - 255).max(1) > 12)[0]
    return col[ink.min() + 2:ink.max() - 1].astype(np.uint8)


def colourbar(fig, rect, colours, top, bottom):
    ax = fig.add_axes(rect)
    ax.imshow(colours[:, None, :], aspect="auto", interpolation="bilinear")
    ax.set_xticks([]); ax.set_yticks([])
    for s in ax.spines.values():
        s.set_linewidth(0.3); s.set_color("#666666")
    ax.text(1.35, 1, top, transform=ax.transAxes, va="top", ha="left")
    ax.text(1.35, 0, bottom, transform=ax.transAxes, va="bottom", ha="left")


def map_axes(fig, rect, pix):
    ax = fig.add_axes(rect)
    ax.imshow(pix, interpolation="none", aspect="auto")
    ax.set_axis_off()
    return ax


# ---------------- Fig. 4: continuous conditioning factors ----------------
img = load(SUBM / "Fig4.jpeg")
panels = [(87, 815, 113, 840), (1210, 1937, 114, 841), (2250, 2975, 113, 840),   # x0, x1, y0, y1 (px)
          (87, 815, 911, 1639), (1210, 1937, 911, 1638), (2250, 2977, 911, 1639)]
bars = [(873, 905, 495, 717), (1971, 2007, 520, 749), (3027, 3059, 482, 701),
        (840, 880, 1275, 1504), (1991, 2025, 1273, 1509), (3021, 3061, 1273, 1488)]
labels = ["Distance (m)", "Saturated\nHydraulic\nConductivity\n(cm/d)", "TWI", "Slope\n(degrees)", "Elevation\n(m)",
          "HAND (m)"]
values = [("3058", "0"), ("16", "3"), ("28.01", "10.25"), ("37.095", "0"), ("139.55", "68.22"), ("88", "0")]
a = img[113:840, 87:815].reshape(-1, 3).astype(int)
stream = np.median(a[(a[:, 2] - a[:, 1] > 40) & (a[:, 2] > 120)], 0) / 255

S, GAP, H = 0.93, 0.665, 2.12          # map side (in), space right of each map (in), figure height (in)
fig = plt.figure(figsize=(TW, H))
for i, ((x0, x1, y0, y1), bar, lab, (vmax, vmin)) in enumerate(zip(panels, bars, labels, values)):
    r, c = divmod(i, 3)
    left, bottom = 0.03 + c * (S + GAP), H - 0.06 - (r + 1) * S - r * 0.1
    map_axes(fig, [left / TW, bottom / H, S / TW, S / H], img[y0:y1, x0:x1])   # published colours (authors' choice)
    xl = left + S + 0.04
    fig.text(xl / TW, (bottom + S) / H, f"({'ABCDEF'[i]})", va="top", fontsize=6.5)
    cb_h = 0.36
    colourbar(fig, [(xl + 0.02) / TW, (bottom + 0.06) / H, 0.06 / TW, cb_h / H], bar_colours(img, *bar), vmax, vmin)
    fig.text(xl / TW, (bottom + 0.06 + cb_h + 0.05) / H, lab, va="bottom", fontsize=6.3, linespacing=1.1)
    if i == 0:
        fig.lines.append(plt.Line2D([xl / TW, (xl + 0.1) / TW], [(bottom + S - 0.22) / H] * 2, color=stream, lw=1.0,
                                    transform=fig.transFigure))
        fig.text((xl + 0.13) / TW, (bottom + S - 0.22) / H, "Streams\nand rivers", va="center", fontsize=6.3,
                 linespacing=1.1)
fig.savefig(OUT / "Fig4.pdf", dpi=800)
plt.close(fig)
print("Fig. 4 done")

# ---------------- Fig. 5: land use and land cover (A) and flood labels (B) ----------------
from matplotlib.patches import Patch  # noqa: E402

img = load(SUBM / "Fig5.jpeg")
A, B = img[29:1435, 32:1429].copy(), img[29:1435, 1499:2694]
# MapBiomas light green of "Other non Vegetated Areas" (110, 226, 110) reads as grassland under deuteranopia: dark grey
PAL5 = np.array([(30, 141, 74), (123, 89, 2), (61, 177, 235), (215, 188, 117), (237, 222, 141), (192, 123, 161),
                 (212, 40, 30), (110, 226, 110), (37, 50, 227)], np.float32)   # legend order below
dist = np.linalg.norm(A[..., None, :].astype(np.float32) - PAL5, axis=-1)
A[(dist.argmin(-1) == 7) & (dist.min(-1) < 60)] = (80, 80, 80)
lulc = [("Forest Formation", (30, 141, 74)), ("Forest Plantation", (123, 89, 2)), ("Wetland", (61, 177, 235)),
        ("Grassland Formation", (215, 188, 117)), ("Pasture", (237, 222, 141)), ("Temporary Crop", (192, 123, 161)),
        ("Urban Area", (212, 40, 30)), ("Other non Vegetated Areas", (80, 80, 80)),
        ("River, Lake and Ocean", (37, 50, 227))]
mh = 2.2                                       # map height (in)
wa, wb = mh * A.shape[1] / A.shape[0], mh * B.shape[1] / B.shape[0]
H = mh + 0.98
fig = plt.figure(figsize=(TW, H))
xa, xb = 0.02, 0.02 + wa + 0.26
map_axes(fig, [xa / TW, (H - 0.03 - mh) / H, wa / TW, mh / H], A)
map_axes(fig, [xb / TW, (H - 0.03 - mh) / H, wb / TW, mh / H], B)
for x, t in ((xa + wa + 0.03, "(A)"), (xb + wb + 0.03, "(B)")):
    fig.text(x / TW, (H - 0.03) / H, t, va="top")
kw = dict(frameon=False, fontsize=6.5, title_fontsize=6.5, handlelength=1.5, handleheight=0.9, borderaxespad=0,
          labelspacing=0.35, alignment="left")
fig.legend(handles=[Patch(fc=np.array(c) / 255, ec="#555555", lw=0.3, label=l) for l, c in lulc], ncol=2,
           title="LEGEND", loc="upper left", bbox_to_anchor=(xa / TW + 0.03, (H - mh - 0.12) / H), columnspacing=1.2,
           **kw)
fig.legend(handles=[Patch(fc="white", ec="black", lw=0.5, label="1   Flood-risk sector"),
                    Patch(fc="black", ec="black", lw=0.5, label="0   Unlabeled")],
           title="LEGEND", loc="upper left", bbox_to_anchor=(xb / TW + 0.02, (H - mh - 0.12) / H), **kw)
fig.savefig(OUT / "Fig5.pdf", dpi=800)
plt.close(fig)
print("Fig. 5 done")


def overlay(img, width, blank):
    """Figure of the given printed width showing the published image with the boxes in `blank` (x0, x1, y0, y1 px)
    whitened; returns the figure, an axes in pixel coordinates and the pixels-per-point factor."""
    img = img.copy()
    for x0, x1, y0, y1 in blank:
        img[y0:y1, x0:x1] = 255
    h, w = img.shape[:2]
    fig = plt.figure(figsize=(width, width * h / w))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.imshow(img, interpolation="none")
    ax.set_xlim(0, w); ax.set_ylim(h, 0); ax.set_axis_off()
    return fig, ax, w / (width * 72)


# ---------------- Fig. 16: flood susceptibility of the five labelling strategies ----------------
img = load(SUBM / "Fig16.jpeg")
frames = [(81, 1737, 80), (1855, 3511, 80), (3621, 5277, 80), (1086, 2741, 1930), (2921, 4577, 1930)]  # x0, x1, top
fig, ax, ppt = overlay(img, TW, [(x1 + 4, x1 + 100, top + 4, top + 110) for _, x1, top in frames] +
                       [(30, 700, 3060, 3730)])
for i, (_, x1, top) in enumerate(frames):
    ax.text(frames[i][0] + 30, top + 30, f"({'ABCDE'[i]})", va="top", fontsize=7)   # inside the frame, top left
ax.legend(handles=[Patch(fc=np.array((254, 215, 176)) / 255, ec="#8a6d4a", lw=0.4, label="Flood hazard\nareas"),
                   Patch(fc=np.array((8, 48, 107)) / 255, ec="none", label="1 - Flood\nsusceptibility"),   # map colour (the QGIS legend had a lighter blue)
                   Patch(fc="white", ec="black", lw=0.4, label="0 - Non-flood\nsusceptibility")],
          title="LEGEND", loc="lower left", bbox_to_anchor=(45 / 5409, 1 - 3800 / 3862), frameon=False, fontsize=6.5,
          title_fontsize=6.5, alignment="left", handlelength=1.4, borderaxespad=0, labelspacing=0.5)
fig.savefig(OUT / "Fig16.pdf", dpi=1200)
plt.close(fig)
print("Fig. 16 done")


# ---------------- Figs. S7 and S8: attention zones (the QGIS legend box is redrawn in place) ----------------
from matplotlib.colors import LinearSegmentedColormap  # noqa: E402
from matplotlib.patches import Polygon, Rectangle  # noqa: E402

BLUES = LinearSegmentedColormap.from_list("qgis_blues", [(247 / 255, 251 / 255, 1), (107 / 255, 174 / 255, 214 / 255),
                                                         (8 / 255, 81 / 255, 156 / 255)])
TWS = 5.15


def zones_legend(fig, img, old, side, fs=6.2, vertical=True):
    """Legend sized to its content (text >= 6 pt) and never smaller than the published legend box old = (x0, x1, y0, y1)
    px, which it covers; anchored at the bottom-left (side="left") or bottom-right corner of that box. Rows: LEGEND,
    attention-zone outline, flood-susceptibility colour bar (vertical, 0 at the top as published, or horizontal)."""
    h, w = img.shape[:2]
    ppt = w / (fig.get_figwidth() * 72)                      # image px per printed point
    x0o, x1o, y0o, y1o = old
    r = fig.canvas.get_renderer()
    def width(txt):
        t = fig.text(0, 0, txt, fontsize=fs); v = t.get_window_extent(r).width * 72 / fig.dpi; t.remove(); return v
    tw = max(width("Flood susceptibility"), 13 + width("Attention zones")) + 2
    lh, pad = fs * 1.3, 4
    yz, yf = pad + 1.2 * lh, pad + 2.4 * lh                  # zone row (top), flood-susceptibility row (top)
    yb = yf + 1.15 * lh                                      # colour bar top
    bh = 2.3 * lh if vertical else 4.5
    H = max(yb + bh + (0.5 * fs if vertical else 1 + fs) + pad, (y1o - y0o) / ppt)
    W = max(tw + 2 * pad, (x1o - x0o) / ppt)
    x0 = x0o if side == "left" else x1o - W * ppt
    lg = fig.add_axes([x0 / w, 1 - y1o / h, W * ppt / w, H * ppt / h])
    lg.set_xticks([]); lg.set_yticks([])
    for sp in lg.spines.values():
        sp.set_linewidth(0.4); sp.set_color("#888888")
    lg.text(pad, pad, "LEGEND", va="top", fontsize=fs)
    for ec, lw in (("black", 1.6), ("#ffd700", 0.8)):
        lg.add_patch(Rectangle((pad, yz), 9, 0.75 * fs, fill=False, ec=ec, lw=lw))
    lg.text(pad + 13, yz + 0.375 * fs, "Attention zones", va="center", fontsize=fs)
    lg.text(pad, yf, "Flood susceptibility", va="top", fontsize=fs)
    if vertical:
        lg.imshow(np.linspace(0, 1, 256)[:, None], cmap=BLUES, extent=(pad, pad + 8, yb + bh, yb), aspect="auto")
        lg.add_patch(Rectangle((pad, yb), 8, bh, fill=False, ec="#888888", lw=0.3))
        for v in (0, 0.5, 1):
            lg.text(pad + 12, yb + v * bh, f"{v:g}", va="center", fontsize=fs)
    else:
        bx, bw = pad + 0.4 * fs, W - 2 * pad - 0.8 * fs           # inset so the end labels stay inside the box
        lg.imshow(np.linspace(0, 1, 256)[None], cmap=BLUES, extent=(bx, bx + bw, yb + bh, yb), aspect="auto")
        lg.add_patch(Rectangle((bx, yb), bw, bh, fill=False, ec="#888888", lw=0.3))
        for v in (0, 0.5, 1):
            lg.text(bx + v * bw, yb + bh + 1, f"{v:g}", va="top", ha="center", fontsize=fs)
    lg.set_xlim(0, W); lg.set_ylim(H, 0)


def yellow_outlines(img):
    """Red zone outlines (long straight red runs; label text is left red) redrawn yellow with a black casing:
    the published red vanishes on the satellite imagery for protanopes."""
    a = img.astype(int)
    red = (a[..., 0] > 150) & (a[..., 0] - a[..., 1] > 80) & (a[..., 0] - a[..., 2] > 80)
    lines = ndimage.binary_opening(red, np.ones((1, 61))) | ndimage.binary_opening(red, np.ones((61, 1)))
    out = img.copy()
    out[ndimage.binary_dilation(lines, iterations=3)] = 0
    out[ndimage.binary_dilation(lines, iterations=1)] = (255, 215, 0)
    return out


# S8 is printed at the text width with three panels, so its zone labels (about 5.5 pt) are redrawn at 7.5 pt,
# right-aligned on the published label boxes (x0, x1, y0, y1 px; va = side kept fixed)
S8_LABELS = [("Attention zone 4", (759, 1321, 36, 115), "top"), ("Attention zone 5", (2219, 2789, 1506, 1585), "bottom"),
             ("Attention zone 6", (3423, 3987, 1486, 1562), "bottom")]
# published legend boxes (with their frame); the new legends cover them, anchored at the same corner
for name, width, box, side, vert in (("FigS7.jpeg", TWS, (2183, 2674, 2817, 3257), "right", True),
                                     ("FigS8.jpeg", TWS, (53, 420, 1173, 1614), "left", False)):
    img = yellow_outlines(load(SUBS / name))
    labels = S8_LABELS if name == "FigS8.jpeg" else []
    fig, ax, _ = overlay(img, width, [(x0 - 6, x1 + 6, y0 - 6, y1 + 6) for _, (x0, x1, y0, y1), _ in labels])
    for text, (x0, x1, y0, y1), va in labels:
        ax.text(x1, y0 if va == "top" else y1, text, ha="right", va=va, fontsize=7.5, family="Times New Roman",
                weight="bold", style="italic", color=(0.8, 0.08, 0.08),
                bbox=dict(boxstyle="square,pad=0.2", fc="white", ec="black", lw=0.5))
    zones_legend(fig, img, box, side, fs=6.2 if vert else 6.0, vertical=vert)
    fig.savefig(OUT / name.replace(".jpeg", ".pdf"), dpi=900)
    plt.close(fig)
print("Figs. S7, S8 done")

def margins(img, frame):
    """Boxes covering everything outside the map frame (where QGIS wrote the coordinate labels)."""
    x0, x1, y0, y1 = frame
    h, w = img.shape[:2]
    return [(0, w, 0, y0 - 3), (0, w, y1 + 4, h), (0, x0 - 3, 0, h), (x1 + 4, w, 0, h)]


def graticule(ax, frame, xs, ys, lon=("47°22.2′W", "47°20.4′W"), lat=("2°58.2′S", "3°0.0′S"), fs=7):
    """Coordinate labels of the published maps, redrawn on the four sides of the frame."""
    x0, x1, y0, y1 = frame
    for x, t in zip(xs, lon):
        ax.text(x, y0 - 10, t, ha="center", va="bottom", fontsize=fs)
        ax.text(x, y1 + 10, t, ha="center", va="top", fontsize=fs)
    for y, t in zip(ys, lat):
        ax.text(x0 - 10, y, t, ha="right", va="center", rotation=90, rotation_mode="anchor", fontsize=fs)
        ax.text(x1 + 10, y, t, ha="left", va="center", rotation=-90, rotation_mode="anchor", fontsize=fs)


def scalebar(ax, x0, x1, ytop, h, fs=7):
    """1 km scale bar (two 500 m segments) redrawn as vector, labels above it."""
    xm = (x0 + x1) / 2
    ax.add_patch(Rectangle((x0, ytop), xm - x0, h, fc="black", ec="black", lw=0.6))
    ax.add_patch(Rectangle((xm, ytop), x1 - xm, h, fc="white", ec="black", lw=0.6))
    for x, t in ((x0, "0"), (xm, "500"), (x1, "1,000 m")):
        ax.text(x, ytop - 10, t, ha="center", va="bottom", fontsize=fs)


# ---------------- Fig. 3: CPRM/SGB flood hazard areas (legend redrawn in its published box) ----------------
from matplotlib.lines import Line2D  # noqa: E402

img = load(SUBM / "Fig3.jpg")
m = img[150:1900, 100:1950].reshape(-1, 3).astype(int)
river = np.median(m[(m[:, 2] - m[:, 0] > 90) & (m[:, 2] > 140)], 0) / 255
# the in-map title box (rows 79-225, under the top frame line) is cut out: the journal keeps titles in the caption
img, d = np.vstack([img[:79], img[226:]]), 226 - 79
FRAME3 = (84, 1990, 76, 1937 - d)                 # map frame of Fig. 3 (x0, x1, y0, y1 px)
# QGIS text left in the map (scale bar labels, datum box) is redrawn as vector; the nominal scale 1:25000 is dropped
# because it does not hold at print size (the scale bar does). The legend box is widened to x = 610 so that the 7 pt
# labels fit; the datum box is whitened with its old border (x 87-473, y 1784-1934; border at x 467, y 1789) and rewritten
fig, ax, _ = overlay(img, TW, [(84, 610, 561 - d, 766 - d), (1490, 1987, 1795 - d, 1933 - d), (87, 473, 1784 - d, 1934 - d)]
                     + margins(img, FRAME3))
graticule(ax, FRAME3, (641, 1857), (875 - d, 1484 - d), lat=("2°59.1′S", "3°0.0′S"))  # 2°58.2′S fell in the cut band
scalebar(ax, 1517, 1881, 1890 - d, 27)
ax.text((87 + 473) / 2, (1784 + 1934) / 2 - d, "Datum: WGS84\nSource: CPRM/SGB", ha="center", va="center", fontsize=7,
        family="Times New Roman", weight="bold", style="italic", linespacing=1.4)
ax.legend(handles=[Line2D([], [], color=river, lw=1.2, label="Rivers and streams"),
                   Patch(fc=np.array((242, 139, 140)) / 255, ec=np.array((143, 87, 83)) / 255, lw=0.8,
                         label="Flood hazard areas")],
          title="LEGEND", loc="upper left", bbox_to_anchor=(90 / img.shape[1], 1 - (566 - d) / img.shape[0]), frameon=False,
          fontsize=7, title_fontsize=7, alignment="left", handlelength=1.6, borderaxespad=0, labelspacing=0.6)
fig.savefig(OUT / "Fig3.pdf", dpi=600, bbox_inches="tight", pad_inches=0.02)
plt.close(fig)
print("Fig. 3 done")

# ---------------- Fig. 18 (submitted Fig. 17): FSIVI map, coordinate labels redrawn ----------------
img = load(SUBM / "Fig17.jpeg").copy()
# the published red-yellow-green-blue ramp is not ordered for protanopes: the FSIVI layer is recoloured with
# RdYlBu_r from the published raster, placed with the graticule (1.8' = 1114 px; r = 0.999 with the published
# colours, display range 0.255-0.943 fitted from them); pixels drawn over the layer (rivers) are kept
CM18, V18 = matplotlib.colormaps["RdYlBu_r"], (0.255, 0.943)
oldbar = img[1934:2197, 115].astype(np.float32)               # published colour bar, top = high
with rasterio.open(DATA / "heat_map_flood_risk_postClassif.tif") as r:
    v, T = r.read(1), r.transform
yy, xx = np.mgrid[:img.shape[0], :img.shape[1]]
ci = np.floor((-47.37 + (xx - 552) / (1114 / 0.03) - T.c) / T.a).astype(int)
ri = np.floor((-2.97 - (yy - 226) / (1114 / 0.03) - T.f) / T.e).astype(int)
inside = (ri >= 0) & (ri < v.shape[0]) & (ci >= 0) & (ci < v.shape[1]) & (xx > 51) & (xx < 1879) & (yy > 43) & (yy < 2270)
val = np.full(img.shape[:2], np.nan)
val[inside] = v[ri[inside], ci[inside]]
layer = np.isfinite(val)
near = binary_dilation(layer, iterations=3) & inside
dd = np.linalg.norm(img[near].astype(np.float32)[:, None, :] - oldbar[None], axis=-1)
ok = dd.min(1) < 30                                           # published ramp colour (not a river drawn on top)
t = np.where(layer[near], (val[near] - V18[0]) / (V18[1] - V18[0]), 1 - dd.argmin(1) / (len(oldbar) - 1))
rows, cols_ = np.where(near)
img[rows[ok], cols_[ok]] = (CM18(np.clip(t[ok], 0, 1))[:, :3] * 255).astype(np.uint8)
# the title box and the north arrow (rows 44-223, under the top frame line) are cut out; the arrow is redrawn
img, d = np.vstack([img[:44], img[224:]]), 224 - 44
FRAME18 = (48, 1882, 40, 2273 - d)
fig, ax, _ = overlay(img, TW, [(55, 380, 1920 - d, 2268 - d), (1385, 1878, 2120 - d, 2262 - d)] + margins(img, FRAME18))
graticule(ax, FRAME18, (552, 1666), (783 - d, 1340 - d), lat=("2°59.1′S", "3°0.0′S"))  # 2°58.2′S fell in the cut band
scalebar(ax, 1404, 1739, 2214 - d, 36)
ax.imshow(np.linspace(1, 0, 256)[:, None], cmap=CM18, extent=(80, 120, 2221 - d, 1934 - d), aspect="auto")
ax.add_patch(Rectangle((80, 1934 - d), 40, 287, fill=False, ec="#666666", lw=0.4))
ax.set_xlim(0, img.shape[1]); ax.set_ylim(img.shape[0], 0)
ax.text(135, 1934 - d, "High\nsusceptibility", va="top", fontsize=7, linespacing=1.1)
ax.text(135, 2221 - d, "Low\nsusceptibility", va="bottom", fontsize=7, linespacing=1.1)
cx, y0 = 1820, 70                                 # north arrow: left half white, right half grey, as in Fig. 3
ax.add_patch(Polygon([(cx, y0), (cx - 38, y0 + 110), (cx, y0 + 80)], closed=True, fc="white", ec="black", lw=0.8))
ax.add_patch(Polygon([(cx, y0), (cx, y0 + 80), (cx + 38, y0 + 110)], closed=True, fc="#9a9a9a", ec="black", lw=0.8))
fig.savefig(OUT / "Fig18.pdf", dpi=600, bbox_inches="tight", pad_inches=0.02)
plt.close(fig)
print("Fig. 18 done")

# ---------------- Fig. 20 (submitted Fig. 19): attention zones, zone labels redrawn as vector text ----------------
# label boxes of the published image (x0, x1, y0, y1 px); the labels are redrawn at the same size, left-aligned
F20_LABELS = [(1, (1520, 1857, 54, 106)), (2, (1186, 1522, 372, 424)), (3, (657, 993, 866, 918)),
              (4, (1471, 1807, 1573, 1625)), (5, (61, 398, 1534, 1586)), (6, (53, 390, 2219, 2271))]
img = yellow_outlines(load(SUBM / "Fig19.jpeg"))
fig, ax, _ = overlay(img, TW, [(x0, x1, y0, y1) for _, (x0, x1, y0, y1) in F20_LABELS])
for k, (x0, x1, y0, y1) in F20_LABELS:
    ax.text(x0 + 8, (y0 + y1) / 2, f"Attention zone {k}", ha="left", va="center", fontsize=7, family="Times New Roman",
            weight="bold", style="italic", color=(0.8, 0.08, 0.08), bbox=dict(boxstyle="square,pad=0.15", fc="white", ec="none"))
fig.savefig(OUT / "Fig20.pdf", dpi=600)
plt.close(fig)
print("Fig. 20 done")

# ---------------- Figs. S4-S6: PCA separability plots (notebook 5.2; its input table is not in the project) ----------
# The plotting areas are kept; the legend boxes (inside the plots) are removed and the grid lines under them
# restored, and tick labels, axis labels and legends are redrawn as vector text. As in the published
# figures, the first principal component has no tick labels.
from matplotlib.lines import Line2D  # noqa: E402,F811

PCA = [("FigS4.png", "slicing classification by HAND", "classification_hand", 2080, [131, 402, 673, 945, 1216, 1487, 1758],
        [456, 770, 1084, 1398, 1711, 2025, 2339]),
       ("FigS5.png", "unsupervised classification", "cluster", 2331, [101, 374, 648, 921, 1195, 1469, 1742],
        [400, 715, 1030, 1345, 1660, 1975, 2290]),
       ("FigS6.png", "semi-supervised classification", "classification", 2205, [128, 393, 658, 924, 1189, 1454, 1719],
        [441, 754, 1068, 1382, 1696, 2010, 2324])]
X0, X1, Y0, Y1 = 208, 2530, 94, 1939                # inside the spines (px)
for name, what, hue, lx0, gy, gx in PCA:
    img = load(SUBS / name)
    pix = img[Y0:Y1, X0:X1].copy()
    box = (lx0 - X0 - 4, X1 - X0, 108 - Y0, 320 - Y0)
    vprof = img[600:600 + 1, :][0]                   # a row outside the legend, for the vertical grid lines
    hprof = img[:, 1200]                              # a column outside the legend, for the horizontal grid lines
    pix[box[2]:box[3], box[0]:box[1]] = 255
    for x in gx:
        if box[0] <= x - X0 < box[1]:
            seg = pix[box[2]:box[3], x - X0 - 3:x - X0 + 4]
            pix[box[2]:box[3], x - X0 - 3:x - X0 + 4] = np.minimum(seg, vprof[None, x - 3:x + 4])
    for y in gy:
        if box[2] <= y - Y0 < box[3]:
            seg = pix[y - Y0 - 3:y - Y0 + 4, box[0]:box[1]]
            pix[y - Y0 - 3:y - Y0 + 4, box[0]:box[1]] = np.minimum(seg, hprof[y - 3:y + 4, None])
    yval = np.polyfit(gy, [80, 60, 40, 20, 0, -20, -40], 1)
    ylo, yhi = np.polyval(yval, Y1 - 0.5), np.polyval(yval, Y0 - 0.5)
    fig = plt.figure(figsize=(0.78 * TWS, 0.78 * TWS * 0.75))   # no title: the caption names the labelling
    ax = fig.add_axes([0.12, 0.122, 0.85, 0.843])
    ax.imshow(pix, extent=(0, 1, ylo, yhi), aspect="auto", interpolation="lanczos")
    ax.set_xlim(0, 1); ax.set_ylim(ylo, yhi)
    ax.set_xticks([(x - X0 + 0.5) / (X1 - X0) for x in gx]); ax.set_xticklabels([])
    ax.set_yticks(range(-40, 81, 20)); ax.tick_params(labelsize=6.5, length=2.5, width=0.5)
    for s in ax.spines.values():
        s.set_linewidth(0.6)
    ax.set_xlabel("Principal Component 1", fontsize=7); ax.set_ylabel("Principal Component 2", fontsize=7)
    ax.legend(handles=[Line2D([], [], ls="", marker="o", ms=3.5, mfc=c, mec="white", mew=0.3, alpha=0.6, label=l)
                       for c, l in (("skyblue", "0 (non-flood)"), ("red", "1 (flood)"))],
              title="Class", loc="upper right", fontsize=6.5, title_fontsize=6.5, framealpha=0.9, edgecolor="#cccccc",
              handletextpad=0.3, borderpad=0.4)
    fig.savefig(OUT / name.replace(".png", ".pdf"), dpi=900)
    plt.close(fig)
print("Figs. S4-S6 done")
