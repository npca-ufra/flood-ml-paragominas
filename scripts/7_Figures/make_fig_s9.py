"""Supplementary Fig. S9: five-class flood-susceptibility map under the two-tier scheme (very high = flood-prone
area of the semi-supervised classification; the rest by the Jenks limits 0.51, 0.64 and 0.75 of the FSIVI).
Drawn at its printed size (0.85 of the supplement text width) as a PDF with vector text; the class raster is
resampled (nearest) at 600 dpi. Rasters are read from scripts/files/ and from the Zenodo FSIVI raster."""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import rasterio
from matplotlib.patches import Patch

HERE = Path(__file__).resolve().parent
FILES = HERE.parent / "files"   # heat_map_flood_risk_postClassif.tif from Zenodo
plt.rcParams.update({"font.family": "Arial", "mathtext.fontset": "custom", "mathtext.rm": "Arial", "mathtext.it": "Arial:italic", "mathtext.bf": "Arial:bold", "pdf.fonttype": 42})

with rasterio.open(FILES / "heat_map_flood_risk_postClassif.tif") as r:
    f, t = r.read(1), r.transform
with rasterio.open(FILES / "heat_map_over_flood_risk_masked_postClassif.tif") as r:
    vh = ~np.isnan(r.read(1))
rest = ~np.isnan(f) & ~vh
cls = np.full(f.shape, np.nan)
cls[rest] = np.digitize(f[rest], [0.51, 0.64, 0.75])   # 0 very low ... 3 high
cls[vh] = 4

colors = ["#2c7bb6", "#abd9e9", "#ffffbf", "#fdae61", "#d7191c"]
labels = ["Very low", "Low", "Moderate", "High", "Very high"]
h, w = f.shape
fig, ax = plt.subplots(figsize=(4.37, 4.61))
# opaque RGB with white outside the domain: a masked (transparent) array gets dark fringes when PDF viewers smooth it
rgb = np.ones(cls.shape + (3,))
for k, c in enumerate(colors):
    rgb[cls == k] = matplotlib.colors.to_rgb(c)
ax.imshow(rgb, interpolation="nearest", extent=[t.c, t.c + t.a * w, t.f + t.e * h, t.f])
ax.set_xlabel("Longitude (°)", fontsize=7); ax.set_ylabel("Latitude (°)", fontsize=7)
ax.tick_params(labelsize=6.5, width=0.6, length=2.5)
for s in ax.spines.values():
    s.set_linewidth(0.6)
handles = [Patch(facecolor=c, edgecolor="0.3", lw=0.5, label=l) for c, l in zip(colors, labels)]
ax.legend(handles=handles[::-1], loc="center left", bbox_to_anchor=(1.02, 0.5), frameon=False, fontsize=7,
          title="Susceptibility", title_fontsize=7)
fig.tight_layout()
(HERE / "output").mkdir(exist_ok=True); fig.savefig(HERE / "output" / "FigS9.pdf", dpi=600, bbox_inches="tight", pad_inches=0.02)
print("Fig. S9 done")
