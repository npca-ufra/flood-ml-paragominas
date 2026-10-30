"""High-resolution versions of the map figures of the submitted manuscript, redrawn with the layout of the
originals. Fig. 1: the main panel of the original location map (study area only, as the journal's policy on
location maps asks), with an Esri World Imagery basemap instead of Google Satellite.
Outputs are PDF with vector text and lines; the basemaps are raster, embedded at 600 dpi."""
import sys
from pathlib import Path

import contextily as cx
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import xyzservices.providers as P
from matplotlib.patches import Rectangle, FancyArrow

HERE = Path(__file__).resolve().parent
OUT = HERE / "output"; OUT.mkdir(exist_ok=True)
plt.rcParams.update({"font.family": "Arial", "mathtext.fontset": "custom", "mathtext.rm": "Arial", "mathtext.it": "Arial:italic", "mathtext.bf": "Arial:bold", "font.size": 6.5, "pdf.fonttype": 42})
SERIF = {"family": "Times New Roman", "style": "italic", "weight": "bold"}
LAT0 = -3.0
M_PER_DEG_LON = 111320.0 * np.cos(np.radians(LAT0))
ESRI = "Esri, Maxar, Earthstar Geographics, and the GIS User Community"


def basemap(ax, bounds, source, zoom):
    img, ext = cx.bounds2img(*bounds, zoom=zoom, source=source, ll=True)
    x0, x1, y0, y1 = ext
    lon = np.degrees(np.array([x0, x1]) / 6378137.0)
    lat = np.degrees(2 * np.arctan(np.exp(np.array([y0, y1]) / 6378137.0)) - np.pi / 2)
    ax.imshow(img, extent=(lon[0], lon[1], lat[0], lat[1]), interpolation="lanczos", zorder=0)
    ax.set_xlim(bounds[0], bounds[2]); ax.set_ylim(bounds[1], bounds[3])


def dms(v, hemi):
    v = abs(v); d = int(v); m = (v - d) * 60
    return f"{d}°{m:.1f}′{hemi}"


import geopandas as gpd
from matplotlib.patches import ConnectionPatch, Patch

# ------------------------------------------------------------------ Fig. 1
RECT = (-47.3834, -3.0257, -47.3321, -2.9652)        # study area, measured on the original figure
B1 = (-47.3862, -3.0372, -47.3292, -2.9598)          # map frame of the original main panel, slightly trimmed
w_deg, h_deg = B1[2] - B1[0], B1[3] - B1[1]


def fig1_main(ax, legend=True, info="EPSG: 4326 WGS84\nImagery: Esri World Imagery"):
    """Main panel of Fig. 1: the study area on Esri World Imagery, with graticule, scale bar and north arrow."""
    basemap(ax, B1, P.Esri.WorldImagery, 17)
    ax.set_aspect("equal")
    lx0, ly0 = B1[0], B1[1]
    for s in ax.spines.values():
        s.set_linewidth(0.8); s.set_color("black")
    # graticule every 1.8' with labels on the four sides, as in the original
    glon, glat = [-47.37, -47.34], [-2.97, -3.00, -3.03]
    for g in glon:
        ax.axvline(g, color="black", lw=0.35, alpha=0.85, zorder=2)
    for g in glat:
        ax.axhline(g, color="black", lw=0.35, alpha=0.85, zorder=2)
    ax.set_xticks(glon); ax.set_xticklabels([dms(g, "W") for g in glon])
    ax.set_yticks(glat); ax.set_yticklabels([dms(g, "S") for g in glat], rotation=90, va="center")
    ax.tick_params(which="both", top=True, right=True, labeltop=True, labelright=True, length=2.5, width=0.5,
                   labelsize=6, pad=1.5)
    for lab in ax.get_yticklabels(which="both"):
        lab.set_rotation(90)
    ax.yaxis.set_tick_params(labelrotation=90)
    # study area
    # yellow with a black casing: the published red outline vanishes on the imagery for protanopes
    for ec, lw in (("black", 2.1), ("#ffd700", 1.1)):
        ax.add_patch(Rectangle(RECT[:2], RECT[2] - RECT[0], RECT[3] - RECT[1], fill=False, ec=ec, lw=lw, zorder=3))
    # information box (bottom centre)
    ix0, iw, ih = B1[0] + 0.315 * w_deg, 0.405 * w_deg, 0.035 * h_deg * (info.count("\n") + 1)
    ax.add_patch(Rectangle((ix0, ly0 + 0.006 * h_deg), iw, ih, fc="#dcdcdc", ec="#9a9a9a", lw=0.4, alpha=0.88, zorder=5))
    ax.text(ix0 + iw / 2, ly0 + 0.006 * h_deg + ih / 2, info, fontdict=SERIF,
            fontsize=6.5, ha="center", va="center", linespacing=1.3, zorder=6)
    # scale bar 0-500-1000 m (bottom right)
    L = 1000 / M_PER_DEG_LON
    sx, sy, sh = B1[2] - 0.075 * w_deg - L, ly0 + 0.02 * h_deg, 0.011 * h_deg
    ax.add_patch(Rectangle((sx - 0.035 * w_deg, ly0 + 0.006 * h_deg), L + 0.10 * w_deg, 0.07 * h_deg, fc="white",
                           ec="none", alpha=0.8, zorder=5))
    ax.add_patch(Rectangle((sx, sy), L / 2, sh, fc="black", ec="black", lw=0.4, zorder=6))
    ax.add_patch(Rectangle((sx + L / 2, sy), L / 2, sh, fc="white", ec="black", lw=0.4, zorder=6))
    for f, t in [(0, "0"), (0.5, "500"), (1, "1,000")]:
        ax.text(sx + f * L, sy + sh + 0.006 * h_deg, t, fontsize=6.5, ha="center", va="bottom", zorder=6)
    ax.text(sx + L + 0.012 * w_deg, sy + sh / 2, "m", fontsize=6.5, ha="left", va="center", zorder=6)
    # north arrow (above the scale bar, below the study-area frame)
    nx, ny = B1[2] - 0.045 * w_deg, ly0 + 0.084 * h_deg
    ax.add_patch(FancyArrow(nx, ny, 0, 0.046 * h_deg, width=0.011 * w_deg, head_width=0.04 * w_deg,
                            head_length=0.032 * h_deg, length_includes_head=True, fc="white", ec="black", lw=0.6, zorder=6))
    ax.text(nx - 0.035 * w_deg, ny + 0.022 * h_deg, "N", fontsize=7.5, fontweight="bold", ha="center", va="center",
            color="white", zorder=6)
    if legend:
        # legend box (bottom left)
        lw_, lh_ = 0.30 * w_deg, 0.085 * h_deg
        ax.add_patch(Rectangle((lx0, ly0), lw_, lh_, fc="white", ec="#555555", lw=0.4, zorder=5))
        ax.text(lx0 + 0.04 * w_deg, ly0 + lh_ - 0.022 * h_deg, "LEGEND", fontsize=7, va="center", zorder=6)
        for ec, lw in (("black", 1.9), ("#ffd700", 0.9)):
            ax.add_patch(Rectangle((lx0 + 0.04 * w_deg, ly0 + 0.022 * h_deg), 0.05 * w_deg, 0.022 * h_deg, fill=False,
                                   ec=ec, lw=lw, zorder=6))
        ax.text(lx0 + 0.11 * w_deg, ly0 + 0.033 * h_deg, "Study area", fontsize=6.5, va="center", zorder=6)


# study area only (the journal's map policy: no location map larger than the study area)
pw = 3.25                                             # map width (in); EPSG:4326 drawn with equal degrees, as in QGIS
ph = pw * h_deg / w_deg
mx, my = 0.36, 0.27
fig = plt.figure(figsize=(pw + 2 * mx, ph + 2 * my))
fig1_main(fig.add_axes([mx / (pw + 2 * mx), my / (ph + 2 * my), pw / (pw + 2 * mx), ph / (ph + 2 * my)]))
fig.savefig(OUT / "Fig1_area.pdf", dpi=600)                 # alternative, if the editor asks
plt.close(fig)
print("Fig1", round(pw + 2 * mx, 2), "x", round(ph + 2 * my, 2), "in")

# locator version (Brazil -> Para -> Paragominas -> study area), as in the submitted figure. It shows a larger
# area than the study area, which the journal's map policy discourages; Fig1_area.pdf
# is the alternative if the editor asks for the change
IBGE = HERE / "inputs" / "ibge"                        # IBGE territorial mesh (servicodados.ibge.gov.br/api/v3/malhas)
br, uf, mun = (gpd.read_file(IBGE / f) for f in ("br.geojson", "br_uf.geojson", "pa_mun.geojson"))
pa, pgm = uf[uf.codarea == "15"], mun[mun.codarea == "1505502"]
GREY, ORANGE, BLUE, YEL = "#d9d9d9", "#E69F00", "#0072B2", "#ffd700"   # Okabe-Ito, colour-blind safe
TW, H = 4.79, 4.45
mh = H - 0.42; mw = mh * w_deg / h_deg; ml = TW - 0.22 - mw
fig = plt.figure(figsize=(TW, H))
axm = fig.add_axes([ml / TW, 0.21 / H, mw / TW, mh / H])
fig1_main(axm, legend=False, info="EPSG: 4326 WGS84\nImagery: Esri World Imagery\nBoundaries: IBGE")

def inset(top, h, bounds, ticks_x, ticks_y, letter):
    x0, y0, x1, y1 = bounds
    aspect = 1 / np.cos(np.radians((y0 + y1) / 2))
    w = h * (x1 - x0) / ((y1 - y0) * aspect)
    a = fig.add_axes([0.24 / TW, (H - top - h) / H, w / TW, h / H])
    a.set_xlim(x0, x1); a.set_ylim(y0, y1); a.set_aspect(aspect)
    a.set_xticks(ticks_x); a.set_xticklabels([f"{abs(t):g}°W" for t in ticks_x])
    a.set_yticks(ticks_y); a.set_yticklabels([f"{abs(t):g}°{'S' if t < 0 else ('N' if t > 0 else '')}" for t in ticks_y],
                                              rotation=90, va="center")
    a.tick_params(labelsize=6, length=2, width=0.4, pad=1)
    for sp in a.spines.values():
        sp.set_linewidth(0.6)
    a.text(0.03, 0.97, letter, transform=a.transAxes, va="top", fontsize=7,
           bbox=dict(boxstyle="square,pad=0.15", fc="white", ec="none"))
    return a

def link(a, b, xy_a, xy_b):                           # grey zoom lines from a box in a to the frame of b
    for p, q in zip(xy_a, xy_b):
        fig.add_artist(ConnectionPatch(p, q, "data", "axes fraction", axesA=a, axesB=b, color="#555555", lw=0.5))

A = inset(0.05, 1.12, (-75.5, -34.5, -33.5, 6.5), [-70, -50], [-20, 0], "(A)")
uf.plot(ax=A, fc=GREY, ec="white", lw=0.3); pa.plot(ax=A, fc=ORANGE, ec="black", lw=0.4)
B = inset(1.33, 1.05, (-59.5, -10.2, -45.5, 3.0), [-55, -50], [-5, 0], "(B)")
mun.plot(ax=B, fc="#fbe3b3", ec="#b08a3e", lw=0.2); pa.boundary.plot(ax=B, color="black", lw=0.5)
pgm.plot(ax=B, fc=BLUE, ec="black", lw=0.4)
C = inset(2.55, 0.72, (-49.0, -3.95, -46.3, -2.3), [-48, -47], [-3], "(C)")
mun.plot(ax=C, fc="#f2f2f2", ec="#bdbdbd", lw=0.3); pgm.plot(ax=C, fc="#bcd9ec", ec=BLUE, lw=0.6)
for ec, lw in (("black", 1.8), (YEL, 0.9)):
    C.add_patch(Rectangle(RECT[:2], RECT[2] - RECT[0], RECT[3] - RECT[1], fill=False, ec=ec, lw=lw, zorder=3))
x0, y0, x1, y1 = pa.total_bounds
A.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, fill=False, ec="#555555", lw=0.5))
link(A, B, [(x0, y0), (x1, y0)], [(0, 1), (1, 1)])
x0, y0, x1, y1 = pgm.total_bounds
B.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, fill=False, ec="#555555", lw=0.5))
link(B, C, [(x0, y0), (x1, y0)], [(0, 1), (1, 1)])
# no zoom lines from (C) to (D): they would cross (B) and (C); the yellow outline links the two panels
axm.text(0.02, 0.985, "(D)", transform=axm.transAxes, va="top", fontsize=7, zorder=7,
         bbox=dict(boxstyle="square,pad=0.15", fc="white", ec="none"))
handles = [Patch(fc="none", ec=YEL, lw=1.2, label="Study area"), Patch(fc=BLUE, ec="black", lw=0.4, label="Paragominas\nmunicipality"),
           Patch(fc=ORANGE, ec="black", lw=0.4, label="Pará State"), Patch(fc=GREY, ec="white", lw=0.4, label="Brazil")]
fig.legend(handles=handles, title="LEGEND", loc="lower left", bbox_to_anchor=(0.2 / TW, 0.2 / H), frameon=False,
           fontsize=6.5, title_fontsize=7, alignment="left", handlelength=1.6, labelspacing=0.45)
fig.savefig(OUT / "Fig1.pdf", dpi=600)                      # used in the manuscript
plt.close(fig)
print("Fig1_locator", TW, "x", H, "in")



# ------------------------------------------------------------------ helpers in Web Mercator (as the GEE map views)
import rasterio
from pyproj import Transformer
from matplotlib.patches import Circle

TO3857 = Transformer.from_crs(4326, 3857, always_xy=True).transform
FILES = HERE.parent / "files"


def merc_bounds(lon0, lat0, lon1, lat1):
    x0, y0 = TO3857(lon0, lat0); x1, y1 = TO3857(lon1, lat1)
    return min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1)


def tiles(ax, b, source, zoom, **kw):
    img, ext = cx.bounds2img(b[0], b[1], b[2], b[3], zoom=zoom, source=source)
    ax.imshow(img, extent=ext, interpolation="lanczos", **kw)


def bare(ax, b):
    ax.set_xlim(b[0], b[2]); ax.set_ylim(b[1], b[3]); ax.set_aspect("equal")
    ax.set_xticks([]); ax.set_yticks([])
    for s in ax.spines.values():
        s.set_visible(False)


IMAGERY = P.Esri.WorldImagery
# light street basemap with street names, the closest freely usable match to the Google map of the original
STREETS = "https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Base/MapServer/tile/{z}/{y}/{x}"

# ------------------------------------------------------------------ Fig. 6 (window located on the original panel B)
sec = gpd.read_file(f"zip://{FILES / 'risk_sectorization_and_streams.zip'}!risk_sectorization/risk_sectorization_PGM.shp", encoding="latin1").to_crs(31983)
fl = sec[sec.tipolo_g1.str.startswith("Inunda")]   # CPRM/SGB process type: the 18 river-flood (Inundacao) sectors; the 3 Alagamento sectors are excluded, as in the GEE scripts
buf = fl.buffer(200).union_all()
B6 = merc_bounds(-47.363762, -2.986234, -47.356652, -2.981229)
buf_m = gpd.GeoSeries([buf], crs=31983).to_crs(3857)
sec_m = gpd.GeoSeries([fl.union_all()], crs=31983).to_crs(3857)
# sample points of the exported dataset inside the window: class 1 (flood) inside the sectors, class 0 (unlabeled)
# in the 200 m buffer (flood_dataset.csv, read through common.load)
sys.path.insert(0, str(HERE.parent / "6_RevisionAnalyses"))
from common import load  # noqa: E402
d = load()
pts = gpd.GeoDataFrame({"classes": d.classes}, geometry=gpd.points_from_xy(d.lon, d.lat), crs=4326).to_crs(3857)
pts = pts.cx[B6[0]:B6[2], B6[1]:B6[3]]
pw6 = 1.53
ph6 = pw6 * (B6[3] - B6[1]) / (B6[2] - B6[0])
fig = plt.figure(figsize=(3 * pw6 + 2 * 0.1, ph6 + 0.2))
for k in range(3):
    ax = fig.add_axes([(k * (pw6 + 0.1)) / (3 * pw6 + 0.2), 0.2 / (ph6 + 0.2), pw6 / (3 * pw6 + 0.2), ph6 / (ph6 + 0.2)])
    tiles(ax, B6, IMAGERY, 17, zorder=0)                 # highest zoom with imagery at this location
    if k == 1:
        buf_m.plot(ax=ax, color="black", zorder=2); sec_m.plot(ax=ax, color="white", zorder=3)
    if k == 2:
        buf_m.plot(ax=ax, color=(0, 0, 25 / 255), zorder=2); sec_m.plot(ax=ax, color="white", zorder=3)
        u, f = pts[pts.classes == 0].geometry, pts[pts.classes == 1].geometry
        ax.scatter(u.x, u.y, s=1.1, c=[(0, 0, 200 / 255)], lw=0, zorder=3.5)
        ax.scatter(f.x, f.y, s=1.1, c=["red"], lw=0, zorder=3.6)
    bare(ax, B6)
    fig.text((k * (pw6 + 0.1) + pw6 / 2) / (3 * pw6 + 0.2), 0.02, ["(A)", "(B)", "(C)"][k], ha="center", va="bottom", fontsize=8)
fig.savefig(OUT / "Fig6.pdf", dpi=600); plt.close(fig)
print("Fig6", round(3 * pw6 + 0.2, 2), "x", round(ph6 + 0.2, 2), "in;", len(pts), "sample points")

# ------------------------------------------------------------------ Fig. 15 (window located on the original panels)
# window of each original panel (top-left lon/lat, m per pixel, size in px) registered on the classification rasters
# (IoU of the red areas 0.87 and 0.86); dashed circles measured on the original panels (px from their top-left)
WIN15 = {"A": (-47.363950, -2.979150, 2.560, 791, 534, "imgPost_UnsupervisedClassified_floodRisk.tif", [(674.5, 168), (64.5, 452)], 28),
         "B": (-47.364450, -2.979400, 2.530, 789, 534, "imgPost_SemiSupervisedClassified_floodRisk.tif", [(706.5, 168), (79.5, 451.5)], 851)}
# the panels show the published rasters; four small patches of the submitted panels (50-300 px, two in each) are not in
# them, because the submitted figure came from another run of the post-processing (authors' choice: keep the rasters)
R15 = 60                                             # circle radius (original px)
pw15 = 2.33
ph15 = pw15 * 534 / 791
fig = plt.figure(figsize=(2 * pw15 + 0.13, ph15 + 0.2))
for k, key in enumerate("AB"):
    lon0, lat0, spx, wpx, hpx, tif, circ, _ = WIN15[key]
    lon1, lat1 = lon0 + wpx * spx / (111320 * np.cos(np.radians(2.985))), lat0 - hpx * spx / 110574
    B15 = merc_bounds(lon0, lat1, lon1, lat0)
    ax = fig.add_axes([k * (pw15 + 0.13) / (2 * pw15 + 0.13), 0.2 / (ph15 + 0.2), pw15 / (2 * pw15 + 0.13), ph15 / (ph15 + 0.2)])
    tiles(ax, B15, STREETS, 16, zorder=0)
    with rasterio.open(FILES / tif) as r:
        m = r.read(1) == 1; ext = rasterio.transform.array_bounds(m.shape[0], m.shape[1], r.transform)
    xa, ya = TO3857(ext[0], ext[1]); xb, yb = TO3857(ext[2], ext[3])
    rgba = np.zeros(m.shape + (4,)); rgba[m] = (250 / 255, 32 / 255, 20 / 255, 0.95)
    ax.imshow(rgba, extent=(xa, xb, ya, yb), interpolation="nearest", zorder=2)
    mpp = (B15[2] - B15[0]) / wpx                    # mercator metres per original pixel
    for (px, py) in circ:
        ax.add_patch(Circle((B15[0] + px * mpp, B15[3] - py * mpp), R15 * mpp, fill=False, ec="#e43fe4", lw=1.3,
                            ls=(0, (3, 2)), zorder=4))
    bare(ax, B15)
    fig.text((k * (pw15 + 0.13) + pw15 / 2) / (2 * pw15 + 0.13), 0.02, ["(A)", "(B)"][k], ha="center", va="bottom", fontsize=8)
fig.savefig(OUT / "Fig15.pdf", dpi=600); plt.close(fig)
print("Fig15", round(2 * pw15 + 0.13, 2), "x", round(ph15 + 0.2, 2), "in")
