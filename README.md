# flood-ml-paragominas

Code and processed data supporting the manuscript *"A reproducible positive-and-unlabeled
learning framework for urban flood-susceptibility mapping without verified non-flood labels:
application to Paragominas, Brazilian Amazon"* (submitted to *Environmental Modelling &
Software*; first revision).

The framework maps urban flood-prone areas in Paragominas (Pará State, Brazilian
Amazon) using open geospatial data and machine learning in Google Earth Engine
(GEE) and Python. All file names and code identifiers are in English; a few GEE
asset IDs and shapefile attribute fields are kept in their original Portuguese
because they reference external artifacts (see *Notes*).

## Repository structure

```
flood-ml-paragominas/
├── scripts/
│   ├── 1_DataExploration_and_InitialDisplay.js     # Initial inspection of the base datasets (GEE)
│   ├── 2.1_Streams_and_RiverDistance.js            # Drainage network and distance-to-rivers raster (GEE)
│   ├── 2.2_SpatialDatasetGeneration.js             # Multi-band raster stack and stratified sampling (GEE)
│   ├── 3.1_SemiSupervised_LabelingAndValidation.ipynb  # PU pipeline: Spy Technique + spatial CV (Python/Colab)
│   ├── 3.2_UnsupervisedSpatialProcessing.js        # Unsupervised clustering and HAND threshold slicing (GEE)
│   ├── 3.3_SemiSupervisedSpatialProcessing.js      # Random Forest semi-supervised classification (GEE)
│   ├── 3.4_SpyThreshold_Sensitivity.ipynb          # Spy labeling sensitivity: thresholds, spy fraction, seeds; Tables S1-S2 (revision; Colab)
│   ├── 4_SpatialPostProcessing.js                  # Urban masking and hotspot filtering (GEE)
│   ├── 5.1_PostProcessingVisualization.js          # FSIVI computation and final visualization (GEE)
│   ├── 5.2_SeparabilityAnalysis.ipynb              # Separability analysis and PCA projections (Python/Colab)
│   ├── 6_RevisionAnalyses/                          # Offline benchmark and analyses added in the revision (see its README)
│   ├── 7_Figures/                                   # Scripts that draw the figures of the revised manuscript (see its README)
│   └── files/                                       # Processed datasets and classified rasters (see DATA.md)
├── DATA.md
├── LICENSE
└── README.md
```

## Data

Processed datasets and classified rasters are in `scripts/files/`. Large files
(the predictor stack, the TWI raster, and the full separability point set) exceed
the repository's size budget and are archived on Zenodo. See `DATA.md` for a
per-file description and the Zenodo location.

## Run order

1. Google Earth Engine (Code Editor): `1_` (inspection) → `2.1_` → `2.2_` (exports `flood_dataset.csv` and the
   predictor stack) → notebook `3.1_` (Colab; derives the labeled set D* and the spatial folds) → `3.2_`, `3.3_` →
   `4_` → `5.1_` (Table 4, FSIVI, Table 7, attention zones; exports the separability point set) → notebook `5.2_`.
2. Offline (no GEE account needed): `scripts/6_RevisionAnalyses/` (benchmark and revision analyses; see its README),
   then `scripts/7_Figures/` (all figures; see its README). Notebook `3.4_` runs directly in Colab from the
   repository files.

## Requirements

- A Google Earth Engine account for the `.js` scripts (Code Editor).
- Python 3.9+ with the versions pinned in `scripts/6_RevisionAnalyses/requirements.txt` (numpy, pandas, scipy,
  scikit-learn >= 1.6, xgboost 2.1, geopandas, rasterio, matplotlib, seaborn, contextily, pillow, statsmodels).
  The notebooks run in Google Colab.
- For `scripts/7_Figures/`: the fonts Arial and Times New Roman (matplotlib falls back to DejaVu Sans otherwise),
  poppler (`pdftoppm`, used for the graphical abstract), internet access (Esri basemap tiles) and a LaTeX
  installation with TikZ (`pdflatex`) for the three diagrams.
- The four large files listed in `DATA.md` (Zenodo) go in `scripts/files/`.

## Running the GEE scripts

The asset paths in the scripts are placeholders: replace `.../assets/ProjetoEnchente/` (and `PATH`/`FOLDER` in
`5.1_`) with your own asset folder (`projects/<project>/assets/<folder>/`) and Drive folder. Each script header
lists the Code Editor imports it expects (`geometry`, `roi`, `setor_risco`, ...). The assets correspond to
repository and Zenodo files as follows: `setor_risco` and the drainage lines = the shapefiles in
`scripts/files/risk_sectorization_and_streams.zip`; `twi_par` = `twi_paragominas.tif` (Zenodo);
`raster_dados_espaciais_inundacao` = `spatial_data_raster_flood.tif` (Zenodo); `datasetInundacao_toAsset` =
`flood_dataset.csv`; `train_val_combined_dataset` and `test_dataset` = the exports of notebook 3.1, regenerated
deterministically from `flood_dataset.csv` (`random_state=42`).

## Running the notebooks

Notebooks `3.1_` and `5.2_` load `flood_dataset.csv` (repository) and `separability_evaluation_data.csv` (Zenodo)
from their URLs and restore the column names of the original GEE exports (Portuguese), which the rest of the code
uses. Their stored outputs are those of the original run (messages in Portuguese; the code was translated
afterwards); the values reported in the manuscript are reproduced offline by `scripts/6_RevisionAnalyses/` and
`scripts/7_Figures/`.

## Notes

- The GEE asset IDs, the band names used by the scripts to read live GEE assets,
  and the shapefile attribute field names are kept in their original Portuguese
  because they reference external artifacts produced/consumed by Google Earth
  Engine. The exported data files in `scripts/files/` and on Zenodo use English
  band/column names.
- The processed data in `scripts/files/` and on Zenodo are released under CC-BY-4.0; the code under the MIT
  License (`LICENSE`). The CPRM/SGB risk sectors and the IBGE territorial meshes in
  `scripts/7_Figures/inputs/ibge/` are open government data redistributed unchanged.

## License

Released under the MIT License — see [LICENSE](LICENSE).

## How to cite

Manuscript: *A reproducible positive-and-unlabeled learning framework for urban flood-susceptibility mapping
without verified non-flood labels: application to Paragominas, Brazilian Amazon* (Environmental Modelling &
Software, under review). Data: Zenodo, concept DOI [10.5281/zenodo.21227777](https://doi.org/10.5281/zenodo.21227777)
(version used by the manuscript: v1.0.0, [10.5281/zenodo.21227778](https://doi.org/10.5281/zenodo.21227778)).
