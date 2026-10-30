# Data availability

All processed datasets and classified rasters supporting the manuscript. File names and column/band names are in
English; values are unchanged from the original exports. The data are released under CC-BY-4.0 (the code of this
repository under the MIT License).

## Tracked in this repository (`scripts/files/`)

| File | Produced by | Description |
|------|-------------|-------------|
| `flood_dataset.csv` | GEE 2.2 | Initial stratified sample set (17,456 records at 15 m spacing inside the 200 m buffer of the CPRM/SGB flood sectors), from which notebook 3.1 and `6_RevisionAnalyses/common.py` derive the labeled set D* (`random_state=42`) |
| `feature_importance_flood.csv` | GEE 3.3 | Random Forest Gini importances per predictor (FSIVI weights, Table 3) |
| `attention_zones.csv` / `.xlsx` | drawn manually | The six attention-zone rectangles of Fig. 20 (field `risk` = FSIVI level), imported by GEE 5.1 |
| `img_{Unsupervised,SemiSupervised}Classified_flood_risk.tif` | GEE 3.2 / 3.3 | Unsupervised (X-Means) and PU-learning classifications |
| `img_SlicedClassified_flood_risk_height{3,4,5}m.tif` | GEE 3.2 | HAND 3/4/5 m sliced classifications |
| `imgPost_SlicedClassifiedHAND_{3,4,5}m_HotSpot.tif` | GEE 4 | Post-processed HAND classifications (urban mask, focal mode, minimum mapping unit) |
| `imgPost_{Unsupervised,SemiSupervised}Classified_floodRisk.tif` | GEE 4 | Post-processed X-Means and PU classifications (Table 4, Figs. 15-16) |
| `flood_risk_zones_postClassif.tif` | GEE 5.1 | Connected components of the PU flood-prone area (8-bit visualization with random colors) |
| `heat_map_over_flood_risk_masked_postClassif.tif` | GEE 5.1 | FSIVI map masked to the PU flood-prone area (very-high class of Table 7) |
| `risk_sectorization_and_streams.zip` | - | Shapefiles `risk_sectorization_PGM.shp` and `rivers_streams_pgm.shp`: the CPRM/SGB flood-risk sectors (open government data) and the drainage lines used by the scripts |

## Archived on Zenodo (large files)

Concept DOI [10.5281/zenodo.21227777](https://doi.org/10.5281/zenodo.21227777) (resolves to the latest version);
version used by the manuscript: v1.0.0, [10.5281/zenodo.21227778](https://doi.org/10.5281/zenodo.21227778)
(CC-BY-4.0, 287.8 MB in total). Place the files in `scripts/files/`.

| File | Size | Description | Used by |
|------|------|-------------|---------|
| `spatial_data_raster_flood.tif` | 28.5 MB | Predictor stack exported by GEE 2.2 (8 bands: distance, elevation, slope, ksat, hand, twi, landcover_classification_2023, classes) | GEE 3.2-5.1; `map_level.py`, `pu_map_stability.py`, `ratio_figures.py` |
| `twi_paragominas.tif` | 182.8 MB | Topographic Wetness Index (SRTM; QGIS/OpenTopography) | GEE 2.2 (asset `twi_par`) |
| `heat_map_flood_risk_postClassif.tif` | 1.3 MB | FSIVI continuous susceptibility map (GEE 5.1) | `fsivi_published.py`; `make_relettered_maps.py` (Fig. 18); `make_fig_s9.py` |
| `separability_evaluation_data.csv` | 75.2 MB | Separability point set: 387,097 points with the three classifications (GEE 5.1) | notebook 5.2 |
