"""Overlap between the PU (semi-supervised) and X-Means flood-prone maps (Sect. 4.3, Fig. 15).

Reads the published classification rasters and writes results/20_pu_xmeans_overlap.csv.
Pixel area from the WGS84 pixel size at the latitude of each row (spherical approximation); the areas are within 0.5% of
those computed in Google Earth Engine (Table 4), and the shares are unaffected."""
from pathlib import Path
import numpy as np, pandas as pd, rasterio

from common import results_dir

HERE = Path(__file__).resolve().parent
FILES = HERE.parent / "files"  # scripts/files in the repository


def read(name):
    with rasterio.open(FILES / name) as r:
        a = r.read(1) == 1
        lat = rasterio.transform.xy(r.transform, np.arange(r.height), 0)[1]
        dx, dy = r.res
    R = 6371008.8
    px = np.radians(dx) * R * np.cos(np.radians(lat)) * np.radians(dy) * R / 1e4   # ha per pixel, per row
    return a, px[:, None]


pu, px = read("imgPost_SemiSupervisedClassified_floodRisk.tif")
xm, _ = read("imgPost_UnsupervisedClassified_floodRisk.tif")
ha = lambda m: float((m * px).sum())
row = {"pu_ha": ha(pu), "xmeans_ha": ha(xm), "both_ha": ha(pu & xm), "pu_only_ha": ha(pu & ~xm),
       "xmeans_only_ha": ha(xm & ~pu), "share_of_pu_in_xmeans_pct": 100 * ha(pu & xm) / ha(pu)}
pd.DataFrame([row]).round(3).to_csv(results_dir("results") / "20_pu_xmeans_overlap.csv", index=False)
print(row)
