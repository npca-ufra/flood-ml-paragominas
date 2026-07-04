# flood-ml-paragominas

Code and processed data supporting the manuscript *"Geospatial machine-learning
framework for urban flood susceptibility mapping: a semi-supervised approach
applied to Paragominas, Brazilian Amazon"* (prepared for submission to *Natural Hazards*).

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
│   ├── 4_SpatialPostProcessing.js                  # Urban masking and hotspot filtering (GEE)
│   ├── 5.1_PostProcessingVisualization.js          # FSIVI computation and final visualization (GEE)
│   ├── 5.2_SeparabilityAnalysis.ipynb              # Separability analysis and PCA projections (Python/Colab)
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

## Requirements

- **Google Earth Engine** account (for the `.js` scripts, run in the GEE Code Editor).
- **Python 3** with `pandas`, `numpy`, `scikit-learn` (>= 1.6, required for
  `NearestCentroid.predict_proba` in the cross-validation notebook), `scipy`, `seaborn`,
  `matplotlib` (for the `.ipynb` notebooks, e.g. in Google Colab).

## Notes

- The GEE asset IDs, the band names used by the scripts to read live GEE assets,
  and the shapefile attribute field names are kept in their original Portuguese
  because they reference external artifacts produced/consumed by Google Earth
  Engine. The exported data files in `scripts/files/` and on Zenodo use English
  band/column names.

## License

Released under the MIT License — see [LICENSE](LICENSE).
