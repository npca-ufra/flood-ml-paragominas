// =============================================================================
// Semi-supervised flood risk classification (Random Forest)
// =============================================================================

// ------------------------------ Steps done in Colab ------------------------------
/*
1) Spy Technique
   - Selects a fraction of positives as "spies" and mixes them with unlabeled data.
   - Uses a probabilistic classifier (Naive Bayes) to estimate P(positive).
   - Establishes a threshold from the distribution of the spies' probabilities (mean, standard deviation or quartile).

2) Reliable Negatives
   - Unlabeled data with P(positive) below the threshold -> reliable negatives.

3) Export combined set
   - Export to EE as 'train_val_combined_dataset' with the final label (e.g.: 'new_class') and 'test_dataset'.
*/

// ------------------------------ Inputs (EE) ----------------------------------
var spatialData = ee.Image(
  '.../ProjetoEnchente/raster_dados_espaciais_inundacao'
);

// Selection of explanatory bands (must match the raster bands)
var bands = [
  'elevacao',
  'distancia',
  'declividade',
  'condutividade_hidraulica_solo',
  'hand',
  'twi'
];

// Export/classification region: geometries derived from the "distancia" band
var region = spatialData.select('distancia').geometry(0);

// ------------------- Combined samples (post-Colab) --------------------------
var training = ee.FeatureCollection(
  '.../assets/ProjetoEnchente/train_val_combined_dataset'
);
print('Training and validation sample example:', training.first());
print('Number of training and validation samples:', training.size());

var test = ee.FeatureCollection(
  '.../assets/ProjetoEnchente/test_dataset'
);
print('Test sample example:', test.first());
print('Number of test samples: ', test.size())
print('Number of unlabeled test samples: ', test.filter(ee.Filter.eq('classes',0)).size())
print('Number of labeled test samples - flood class 1: ', test.filter(ee.Filter.eq('classes',1)).size())

// ---------------------------- RF classifier ----------------------------------
// RF is robust to noise and to correlations between variables.
var rf = ee.Classifier.smileRandomForest({
  numberOfTrees: 100,}).train({
  features: training,
  classProperty: 'new_class', // label coming from Colab
  inputProperties: bands
});

// ----------------------- Metrics -------------------------------
// Validation (test)
var tested = test.classify(rf);
var testMatrix = tested.errorMatrix('classes', 'classification');
print('Recall on test data (producer accuracy):', testMatrix.producersAccuracy().get([1,0])); //produceraccuracy is the recall

// Variable importance
var explanation = rf.explain();
print('Classifier explanation:', explanation);

// Classify image (explanatory bands only)
var classifiedImage = spatialData
  .select(bands)
  .clip(region)
  .classify(rf);

// Binary visualization: 0 = no flood; 1 = flood
Map.addLayer(
  classifiedImage,
  {bands: ['classification'], min: 0, max: 1, palette: ['ffffff', 'ff0606']},
  'Classified image (RF)',
  true
);

// -------------------- Post-processing (smoothing) ----------------------------
// Reduces the "salt-and-pepper" effect without altering coherent masses.
var smoothedImage = classifiedImage
  .unmask(0)
  .focal_mode({ radius: 1, units: 'pixels' }); // 3x3 window

Map.addLayer(
  smoothedImage,
  {bands: ['classification'], min: 0, max: 1, palette: ['ffffff', 'ff0606']},
  'Classified image (smoothed)',
  false
);

// ---------------------- Reference layer (CPRM) -------------------------------
Map.addLayer(
  setor_risco.filter(ee.Filter.eq('tipolo_g1', 'Inundação')),
  {},
  'Risk Sectors - CPRM/SGB',
  false
);

// ------------------------------- Exports -------------------------------------
var assetPathEnchente = '.../assets/ProjetoEnchente/';

// Export classified raster (smoothed)
Export.image.toAsset({
  image: smoothedImage.select('classification'),
  assetId: assetPathEnchente + 'img_ClassificadaSemiSuperv_risco_inund',
  description: 'img_ClassificadaSemiSuperv_risco_inund',
  region: region,
  scale: 10,
  maxPixels: 1e10
});
Export.image.toDrive({
  image: smoothedImage.select('classification'),
  description: 'img_ClassificadaSemiSuperv_risco_inund',
  folder:"projetoEnchenteAssets",
  region: region,
  scale: 10,
  maxPixels: 1e10
});

// Export variable importance (table)
var importanceDict = ee.Dictionary(explanation.get('importance'));
var importanceFeature = ee.Feature(ee.Geometry.Point([0, 0]), importanceDict);
var attributeImportanceFlood = ee.FeatureCollection([importanceFeature]);

Export.table.toAsset({
  collection: attributeImportanceFlood,
  description: 'importancia_atributos_inund',
  assetId: assetPathEnchente + 'importancia_atributos_inund'
});

Export.table.toDrive({
  collection: attributeImportanceFlood,
  description: 'importancia_atributos_inund',
  folder: 'projetoEnchenteAssets'
});
