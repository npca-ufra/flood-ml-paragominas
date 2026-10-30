# 7 – Figures of the revised manuscript (ENVSOFT-D-26-02946, first revision)

Scripts that draw the 20 figures of the manuscript, the 10 of the Supplementary Material and the
graphical abstract as PDF files with vector text and embedded fonts, at the printed size (text width
4.79 in in the manuscript, 5.15 in in the Supplementary Material). Outputs go to `output/`.

| Script | Figures | Inputs |
|---|---|---|
| `make_faithful_charts.py` | Figs. 7, 9, 13, 14, 19; S1–S3. Charts redrawn from the published data with the plotting code of notebook 3.1 | `../files/flood_dataset.csv`, `../files/feature_importance_flood.csv`, `inputs/fsivi_values_domain.npy` (FSIVI values over the analyzed area); uses `../6_RevisionAnalyses/common.py` |
| `make_relettered.py` | Figs. 11, 12. Plotted data of the original run kept; axes, labels and legends redrawn as vector text | `inputs/Fig11_original_run.png`, `inputs/Fig12.png` |
| `make_relettered_maps.py` | Figs. 3, 4, 5, 16, 18, 20; S4–S8. Map layers of the submitted figures kept; legends, scale bars, coordinates and labels redrawn; Fig. 18 re-rendered from the FSIVI raster | `inputs/Fig*.jpeg`, `inputs/FigS*.png/.jpeg`; `../files/heat_map_flood_risk_postClassif.tif` (Zenodo) |
| `make_maps_faithful.py` | Figs. 1, 6, 15 (and `Fig1_area.pdf`, a version showing only the study area). Esri basemaps are downloaded at run time | `inputs/ibge/*.geojson` (IBGE territorial mesh), `../files/risk_sectorization_and_streams.zip`, `../files/flood_dataset.csv`, `../files/imgPost_*ClassifiedfloodRisk.tif` |
| `make_fig_s9.py` | Fig. S9 | `../files/heat_map_flood_risk_postClassif.tif` (Zenodo), `../files/heat_map_over_flood_risk_masked_postClassif.tif` |
| `Fig2.tex`, `Fig8.tex`, `Fig10.tex` | Figs. 2, 8, 10 (TikZ diagrams; compile with `pdflatex`) | – |
| `make_graphical_abstract.py` | Graphical abstract | `output/Fig18.pdf` (run after `make_relettered_maps.py`) |

Figs. 17 and S10 are drawn by `../6_RevisionAnalyses/ratio_figures.py`.

`inputs/` holds the raster images of the submitted manuscript (Figs. 3, 4, 5, 12, 16, 17, 19 and S4–S8;
`Fig11_original_run.png` is the original export of Fig. 11), on which the relettered figures are based.
Figure numbers refer to the revised manuscript (submitted Figs. 17–19 are revised Figs. 18–20).

```
python make_faithful_charts.py
python make_relettered.py
python make_relettered_maps.py
python make_maps_faithful.py
python make_fig_s9.py
python make_graphical_abstract.py
cd output && for f in Fig2 Fig8 Fig10; do pdflatex ../$f.tex; done
```
