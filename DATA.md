# Data availability

All processed datasets and classified rasters supporting the manuscript. File
names and column/band names are in English; values are unchanged from the
original exports.

## Tracked in this repository (`scripts/files/`)

| File | Description |
|------|-------------|
| `flood_dataset.csv` | Initial stratified sample (17,456 records) read by the semi-supervised pipeline |
| `feature_importance_flood.csv` | Random Forest Gini importances per predictor (FSIVI weights) |
| `attention_zones.csv` / `.xlsx` | Attention zones used in post-processing |
| `img_{Unsupervised,SemiSupervised}Classified_flood_risk.tif` | Unsupervised and PU-learning classifications |
| `img_SlicedClassified_flood_risk_height{3,4,5}m.tif` | HAND 3/4/5 m sliced classifications |
| `imgPost_SlicedClassifiedHAND_{3,4,5}m_HotSpot.tif` | Post-processed HAND hotspots |
| `imgPost_{Unsupervised,SemiSupervised}Classified_floodRisk.tif` | Post-processed classifications |
| `flood_risk_zones_postClassif.tif` | Final attention-zones raster |
| `heat_map_over_flood_risk_masked_postClassif.tif` | FSIVI map masked to the semi-supervised classification |
| `risk_sectorization_and_streams.zip` | CPRM/SGB risk-sector and drainage shapefiles |

## Archived on Zenodo (large files)

The following exceed the repository size budget and are openly archived on
Zenodo (DOI: [10.5281/zenodo.21227778](https://doi.org/10.5281/zenodo.21227778)):

| File | Description |
|------|-------------|
| `spatial_data_raster_flood.tif` | Stacked predictor composite (8 bands: distance, elevation, slope, ksat, hand, twi, landcover_classification_2023, classes) |
| `twi_paragominas.tif` | Topographic Wetness Index raster (SRTM-derived) |
| `separability_evaluation_data.csv` | Separability evaluation point set (387,097 points) |
| `heat_map_flood_risk_postClassif.tif` | FSIVI continuous susceptibility map |
