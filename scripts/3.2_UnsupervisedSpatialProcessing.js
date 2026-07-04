// =============================================================================
// Unsupervised classification by Clustering and Classification by threshold slicing over HAND
// Base set: multiband raster "dados_espaciais_inundacao"
// =============================================================================

// --------------------------- Load stack --------------------------------------
// Contains bands such as: elevacao, distancia, declividade, hand, (...)
var spatialData = ee.Image(
  '.../assets/ProjetoEnchente/raster_dados_espaciais_inundacao'
);
Map.addLayer(spatialData, {}, 'spatial_data', false);
print('Spatial stack (input):', spatialData);

// Select bands used in the clustering
var bands = ['elevacao', 'distancia', 'declividade', 'hand'];
spatialData = spatialData.select(bands);

// Working region: geometry derived from the "distancia" band
// NOTE: keep consistency with the project's ROI (can be replaced by `geometry`).
var region = spatialData.select('distancia').geometry(0);

// ------------------- Unsupervised clustering (XMeans) ------------------------
// Source: Weka XMeans (k ranging up to 10, starting from 2 clusters).
// Spatial patterns are explored without prior labels.
var newData = ee.FeatureCollection(
  '.../assets/ProjetoEnchente/datasetInundacao_toAsset'
);

var clusterer = ee.Clusterer.wekaXMeans(2, 10).train(newData, bands);

var clusteredImage = spatialData.cluster(clusterer);
// Random visualization for inspection
Map.addLayer(
  clusteredImage.clip(region).randomVisualizer(),
  {},
  'Clustering (KMeans)',
  false
);

// ----------------------- Post-cluster smoothing ------------------------------
// Reduce "salt-and-pepper noise" (isolated pixels).
// Strategy: 3x3 focal mode over the "cluster" band.
var clusteredImageSmooth = clusteredImage
  .unmask(0) // avoids nodata in the neighborhood
  .focal_mode({
    radius: 1,           // 1 pixel -> 3x3 window
    units: 'pixels'
  });


// Binary palette for visualization (assuming up to 2 clusters; adjust as per output)
Map.addLayer(
  clusteredImageSmooth,
  {bands: ['cluster'], min: 0, max: 1, palette: ['ffffff', 'ff0606']},
  'Clustered image (smoothed)'
);

// ============================== HAND (slicing) ==============================
// Global 30 m HAND - https://gee-community-catalog.org/projects/hand/
var handPalette = [
  '023858','006837','1a9850','66bd63','a6d96a','d9ef8b',
  'ffffbf','fee08b','fdae61','f46d43','d73027'
];
var handVis = { min: 1, max: 150, palette: handPalette };

// Reuses the "hand" band from the loaded stack (consistent with the clustering).
var hand = spatialData.select('hand').clip(region)
  .rename('hand')
  .reproject({ crs: 'EPSG:4326', scale: 10 });

Map.addLayer(hand, handVis, 'HAND (m) - from the stack', false);

// Slicing by height-above-drainage threshold
var palettes = require('users/gena/packages:palettes');

var floodHeight_5m = 5; // m - pixels with HAND <= 5 m
var maskHand = hand.gte(0).and(hand.lte(floodHeight_5m));
// Binary classification by HAND (0/1) for potentially floodable area
var classifiedHand_5m = hand.updateMask(maskHand).rename('classification_hand');
Map.addLayer(
  classifiedHand_5m,
  { palette: palettes.cb.Blues[7], min: 0, max: floodHeight_5m },
  'Classified by HAND <= ' + floodHeight_5m + ' m',
  true);

var floodHeight_4m = 4; // m - pixels with HAND <= 5 m
var maskHand = hand.gte(0).and(hand.lte(floodHeight_4m));
// Binary classification by HAND (0/1) for potentially floodable area
var classifiedHand_4m = hand.updateMask(maskHand).rename('classification_hand');
Map.addLayer(
  classifiedHand_4m,
  { palette: palettes.cb.Blues[7], min: 0, max: floodHeight_4m },
  'Classified by HAND <= ' + floodHeight_4m + ' m',
  true);

var floodHeight_3m = 3; // m - pixels with HAND <= 5 m
var maskHand = hand.gte(0).and(hand.lte(floodHeight_3m));
// Binary classification by HAND (0/1) for potentially floodable area
var classifiedHand_3m = hand.updateMask(maskHand).rename('classification_hand');
Map.addLayer(
  classifiedHand_3m,
  { palette: palettes.cb.Blues[7], min: 0, max: floodHeight_3m },
  'Classified by HAND <= ' + floodHeight_3m + ' m',
  true);

// ----------------------- Reference layer (CPRM) ------------------------------
Map.addLayer(
  setor_risco.filter(ee.Filter.eq('tipolo_g1', 'Inundação')),
  {},
  'Risk Sectors - CPRM'
);

// -------------------------- Export cluster -----------------------------------
var assetPathEnchente = '.../assets/ProjetoEnchente/';

Export.image.toAsset({
  image: clusteredImageSmooth.select('cluster'), // exports only the cluster band
  assetId: assetPathEnchente + 'img_ClassificadaNaoSuperv_risco_inund',
  description: 'img_ClassificadaNaoSuperv_risco_inund',
  region: region,
  scale: 10,
  maxPixels: 1e7
});
Export.image.toDrive({
  image: clusteredImageSmooth.select('cluster'),
  description: 'img_ClassificadaNaoSuperv_risco_inund',
  folder:"projetoEnchenteAssets",
  region: region,
  scale: 10,
  maxPixels: 1e10
});

// -------------------- Export HAND classification -----------------------------
Export.image.toAsset({
  image: classifiedHand_5m,
  assetId: assetPathEnchente + ('img_ClassificadaSliced_risco_inund_alt' + floodHeight_5m + 'm'),
  description: 'img_ClassificadaSliced_risco_inund_alt' + floodHeight_5m + 'm',
  region: region,
  scale: 10,
  maxPixels: 1e7
});
Export.image.toDrive({
  image: classifiedHand_5m,
  description: 'img_ClassificadaSliced_risco_inund_alt' + floodHeight_5m + 'm',
  folder:"projetoEnchenteAssets",
  region: region,
  scale: 10,
  maxPixels: 1e10
});

Export.image.toAsset({
  image: classifiedHand_4m,
  assetId: assetPathEnchente + ('img_ClassificadaSliced_risco_inund_alt' + floodHeight_4m + 'm'),
  description: 'img_ClassificadaSliced_risco_inund_alt' + floodHeight_4m + 'm',
  region: region,
  scale: 10,
  maxPixels: 1e7
});
Export.image.toDrive({
  image: classifiedHand_4m,
  description: 'img_ClassificadaSliced_risco_inund_alt' + floodHeight_4m + 'm',
  folder:"projetoEnchenteAssets",
  region: region,
  scale: 10,
  maxPixels: 1e10
});

Export.image.toAsset({
  image: classifiedHand_3m,
  assetId: assetPathEnchente + ('img_ClassificadaSliced_risco_inund_alt' + floodHeight_3m + 'm'),
  description: 'img_ClassificadaSliced_risco_inund_alt' + floodHeight_3m + 'm',
  region: region,
  scale: 10,
  maxPixels: 1e7
});
Export.image.toDrive({
  image: classifiedHand_3m,
  description: 'img_ClassificadaSliced_risco_inund_alt' + floodHeight_3m + 'm',
  folder:"projetoEnchenteAssets",
  region: region,
  scale: 10,
  maxPixels: 1e10
});
