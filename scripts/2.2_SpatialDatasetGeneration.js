// =============================================================================
// Layers for flood modeling - Paragominas/PA
// Description: loads HAND, DTM (ANADEM), slope, TWI, Ksat (HiHydroSoil),
//              distance to drainages, land use/cover (MapBiomas) and generates
//              stratified samples (class 1 = flood; 0 = unlabeled).
// Preconditions (defined outside this snippet):
//   - geometry: ee.Geometry/ee.FeatureCollection of the study area (ROI).
//   - setor_risco: ee.FeatureCollection (CPRM/SGB) with risk typology.
// Notes:
//   - CRS EPSG:4326 was kept (as in the original code).
// =============================================================================


// --------------------------- HAND (30 m) -------------------------------------
// Source: https://gee-community-catalog.org/projects/hand/
var handPalette = [
  '023858', '006837', '1a9850', '66bd63', 'a6d96a', 'd9ef8b',
  'ffffbf', 'fee08b', 'fdae61', 'f46d43', 'd73027'
];
var handVis = { min: 1, max: 150, palette: handPalette };

//  use the "hand-1000" variant (flow threshold = 1000) for HAND.
var hand30m1000 = ee.Image('users/gena/GlobalHAND/30m/hand-1000').clip(geometry);

var hand = hand30m1000.resample('bilinear')
  .rename('hand')
  .reproject({ crs: 'EPSG:4326', scale: 10 });

Map.addLayer(hand, handVis, 'HAND (1000), 30 m (m)', false);


// ----------------------------- ANADEM (DTM) ----------------------------------
// Source: https://www.ufrgs.br/hge/anadem-modelo-digital-de-terreno-mdt/
var anadem = ee.Image('projects/et-brasil/assets/anadem/v1');

// Remove noData (-9999) and clip to the ROI.
var elevationM = anadem
  .updateMask(anadem.neq(-9999))
  .clip(geometry).resample('bilinear')
  .rename('elevacao')
  .reproject({ crs: 'EPSG:4326', scale: 10 });

var elevationVis = {
  min: 70,
  max: 152.0,
  palette: ['006600', '002200', 'fff700', 'ab7634', 'c4d0ff', 'ffffff']
};

Map.addLayer(elevationM, elevationVis, 'Elevation (m)', false);


// --------------------------- Slope (degrees) ---------------------------------
// slope provides geomorphological context for susceptible areas.
var slopeDegrees = ee.Terrain.slope(elevationM)
  .rename('declividade')
  .reproject({ crs: 'EPSG:4326', scale: 10 });

Map.addLayer(
  slopeDegrees,
  { min: 0, max: 10, palette: ['green', 'yellow', 'red'] },
  'Slope (degrees)',
  false
);

// ---------------------------- TWI (dimensionless) ----------------------------
// Topographic Wetness Index computed externally (QGIS).
var twiVis = {
  min: 0, max: 30,
  palette: ['#f7fbff','#deebf7','#c6dbef','#9ecae1','#6baed6','#4292c6','#2171b5','#084594']
};

var twiQgis = ee.Image('.../assets/ProjetoEnchente/twi_par')
  .clip(geometry)
  .resample('bilinear')
  .rename('twi')
  .reproject({ crs: 'EPSG:4326', scale: 10 });

Map.addLayer(twiQgis, twiVis, 'TWI (dimensionless wetness index)');


// ----------------- Soil Hydraulic Conductivity (Ksat) ------------------------
// HiHydroSoil v2.0 - https://gee-community-catalog.org/projects/hihydro_soil/#citation-related-publications
var palettesGena = require('users/gena/packages:palettes');
var ksatVis = { min: 3, max: 16, palette: palettesGena.cmocean.Delta[7] };

var ksatCollection = ee.ImageCollection('projects/sat-io/open-datasets/HiHydroSoilv2_0/ksat');
var ksatBase = ksatCollection.first().multiply(0.0001).clip(geometry); // adjusts scale

// Gap-filling strategy:
// 1) Set a sentinel value (1000) for noData; 2) replace with neighbors' median;
// 3) apply bilinear resampling to smooth transitions.
var ksatUnmask = ksatBase.unmask(1000);
var ksatMissingMask = ksatUnmask.eq(1000);

var ksatNeighborsMedian = ksatUnmask.focal_median({
  radius: 45, kernelType: 'square', units: 'pixels'
});

var ksatFilled = ksatUnmask.where(ksatMissingMask, ksatNeighborsMedian)
  .resample('bilinear')
  .rename('condutividade_hidraulica_solo')  // cm/d
  .reproject({ crs: 'EPSG:4326', scale: 10 });

Map.addLayer(ksatFilled, ksatVis, 'Ksat (cm/d) - filled (bilinear)', true);


// --------------------- Distance to the nearest river branch ------------------
// Euclidean distance (m) to drainages - asset produced previously.
var distRivers = ee.Image('.../assets/ProjetoEnchente/distancia_rios')
  .rename('distancia')
  .reproject({ crs: 'EPSG:4326', scale: 10 });

var distVis = { min: 0, max: 750, palette: ['blue', 'green', 'yellow', 'red'] };
Map.addLayer(distRivers, distVis, 'Distance to rivers (m)', false);


// --------------- Land use and land cover (MapBiomas S2 Beta) -----------------
// Source: https://brasil.mapbiomas.org/codigos-e-ferramentas/
var finalYear = 2023;

var mapbiomasPal = require('users/mapbiomas/modules:Palettes.js').get('classification9');
var mapbiomasVis = { min: 0, max: 69, palette: mapbiomasPal, format: 'png' };

//var lulcS2 = ee.Image('projects/mapbiomas-public/assets/brazil/lulc/collection_S2_beta/collection_LULC_S2_beta')
//  .clip(geometry);
var lulcS2 = ee.Image('projects/mapbiomas-public/assets/brazil/lulc_10m/collection2/mapbiomas_10m_collection2_integration_v1')
  .clip(geometry);

var landCover2023 = lulcS2
  .select('classification_' + finalYear)
  .rename('usocobersolo_classification_2023');

Map.addLayer(landCover2023, mapbiomasVis, 'Land cover and use (10 m) - ' + finalYear, false);

/*
Examples of MapBiomas classes:
 3  - Forest Formation                    #1f8d49
 9  - Forest Plantation                   #7a5900
 11 - Wetland/Marsh Area                  #519799
 12 - Grassland Formation                 #d6bc74
 15 - Pasture                             #edde8e
 19 - Temporary Crop                      #C27BA0
 24 - Urban Area                          #d4271e
 25 - Other Non-Vegetated Areas           #db4d4f
 33 - River, Lake and Ocean               #2532e4
*/

// ------------------ Risk Sectors (CPRM/SGB) - Flooding -----------------------
// Source: https://geoportal.sgb.gov.br/desastres/
var riskSector = ee.FeatureCollection(setor_risco) // shape of the risk regions over Paragominas/PA
  .filter(ee.Filter.eq('tipolo_g1', 'Inundação'));

Map.addLayer(riskSector, {}, 'Risk Sector - Flooding (CPRM)', false);

// 200 m buffer around the risk polygons to compose class 0.
var riskSectorBuffer200m = riskSector.geometry().buffer(200, 0);
Map.addLayer(riskSectorBuffer200m, {}, 'Risk Sector - 200 m buffer', false);

// ---------------------- Stacking of explanatory bands ------------------------
// gather physical/hydrological variables + land use/cover.
var spatialBands = distRivers
  .addBands(elevationM)
  .addBands(slopeDegrees)
  .addBands(ksatFilled)
  .addBands(hand)
  .addBands(twiQgis)
  .addBands(landCover2023);


// -------------------------- Class mask (0/1) ---------------------------------
// Rule: 1 = flood (inside the risk polygons); 0 = unlabeled (buffer).
var classesBase = ee.Image(0).clip(riskSectorBuffer200m);
var floodClass = ee.Image(1).clip(riskSector);

var classes = classesBase.add(floodClass).unmask().clip(riskSectorBuffer200m);
Map.addLayer(classes, {}, 'Classes: 1 = flood; 0 = unlabeled', false);

// Append the classes band to the main stack.
spatialBands = spatialBands.addBands(classes.rename('classes'));


// ----------------------------- Sampling --------------------------------------
// stratified sampling to balance classes at 10 m.
var dataset = spatialBands.stratifiedSample({
  numPoints: 0,                 // ignored when using classValues/classPoints
  classBand: 'classes',
  classValues: [0, 1],
  classPoints: [40000, 5000],   // adjust according to coverage/area
  region: riskSectorBuffer200m,
  scale: 15, //##
  geometries: true
});

Map.addLayer(dataset, { color: 'blue' }, 'Sample points (pixels)', false);
print('Number of samples:', dataset.size());
print('Unlabeled samples (0): ',dataset.filter(ee.Filter.eq('classes',0)).size()) //##
print('Positive flood-labeled samples (1): ',dataset.filter(ee.Filter.eq('classes',1)).size()) //##


// ------------------------------ Exports --------------------------------------
// the raster export region is defined by the geometry of `distRivers`,
var assetPathEnchente = '.../assets/ProjetoEnchente/';

Export.table.toDrive({
  collection: dataset,
  description: 'datasetInundacao_toDrive',
  folder:"projetoEnchenteAssets",
});

Export.table.toAsset({
  collection: dataset,
  description: 'datasetInundacao_toAsset',
  assetId: assetPathEnchente + 'datasetInundacao_toAsset'
});

Export.image.toAsset({
  image: spatialBands,
  description: 'raster_dados_espaciais_inundacao',
  assetId: assetPathEnchente + 'raster_dados_espaciais_inundacao',
  region: distRivers.geometry(0),
  crs: 'EPSG:4326',
  scale: 10,
  maxPixels: 1e10
});

print("Band types:" ,spatialBands.bandTypes())
spatialBands = spatialBands.toFloat()

Export.image.toDrive({
  image: spatialBands,
  description: 'raster_dados_espaciais_inundacao',
  folder:"projetoEnchenteAssets",
  region: distRivers.geometry(0),
  //crs: 'EPSG:4326',
  scale: 10,
  maxPixels: 1e10
});

//=========================================
//After exporting the training data samples, perform the following steps in Google Colab

/*
1 - Spy Technique. Selects a fraction of the positives as "spies" and mixes them with unlabeled data. Uses a simple probabilistic classifier to compute probabilities and extract reliable negatives.
2 - Use the distribution of the spies' probabilities to define a threshold. Unlabeled data with probability below this threshold are considered reliable negatives.
*/
//=========================================
//Then import the samples and perform the rest of the procedure in GEE, which initially consists of:=======================
/*
3 - Use a robust classifier with the unlabeled data as reliable negatives to train the model in the normal training process.
*/
//=========================================
