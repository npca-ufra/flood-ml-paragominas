/***************************************************************
 * PROJECT: Urban Flood Susceptibility Mapping
 * PLATFORM: Google Earth Engine (JavaScript)
 * AUTHOR: Gilberto Junior
 * DESCRIPTION:
 *  1) Area-level metrics of the classified maps (HAND 3/4/5 m, X-Means,
 *     semi-supervised PU) against the CPRM/SGB flood sectors over the
 *     urban area (MapBiomas, class 24) - Table 4
 *  2) Export of samples for the separability analysis (Python)
 *  3) FSIVI index (susceptibility map weighted by variable importance),
 *     descriptive statistics and histogram
 *  4) Two-tier susceptibility classes - Table 7
 *  5) Attention zones, animation (GIF) and exports
 *
 * REQUIRED IMPORTS:
 *   geometry        - study area (rectangle)
 *   setor_risco     - CPRM/SGB risk sectors (FeatureCollection)
 *   geometry_forgif - clipping region used for the exports and the animation
 *   point_text      - position of the label in the animation
 *   regioes_atencao_inicioDaInund99/96/95/90/89/88 - attention zones
 *
 * Asset IDs, band names read from the assets and shapefile fields
 * (e.g. 'elevacao', 'tipolo_g1') keep their original Portuguese names.
 ***************************************************************/


// ==================================================================
// 0) PARAMETERS AND HELPER FUNCTIONS
// ==================================================================
var PATH   = '../';
var FOLDER = '../';
var CRS    = 'EPSG:4326';
var SCALE  = 10;  // m

// Area (ha) of the valid (unmasked) pixels of an image within geometry
var areaHa = function (img) {
  var pixelHa = ee.Image.pixelArea().divide(1e4)
    .updateMask(img.mask().reduce(ee.Reducer.min()).gt(0));
  return ee.Number(pixelHa.reduceRegion({
    reducer: ee.Reducer.sum(),
    geometry: geometry,
    crs: CRS,
    scale: SCALE,
    maxPixels: 1e11
  }).get('area'));
};

var paletteFSIVI = ['22dd0e', 'f9fe31', 'd70c0c'];
var visFSIVI = {bands: ['suscetibilidade_inundacao'], min: 0.3699895127314622,
                max: 0.9534484538232613, palette: paletteFSIVI};


// ==================================================================
// 1) INPUT DATA
// ==================================================================
var spatialData = ee.Image(PATH + 'raster_dados_espaciais_inundacao');

// Urban mask (MapBiomas 2023, class 24)
var urbanImg = spatialData.select('usocobersolo_classification_2023')
  .eq(24).selfMask().clip(geometry).rename('urban');

// CPRM/SGB flood sectors (vector and raster)
var floodSectors = setor_risco.filter(ee.Filter.eq('tipolo_g1', 'Inundação'));
var sectorsImg = ee.Image(0).byte().paint(floodSectors, 1).selfMask()
  .reproject({crs: CRS, scale: SCALE}).rename('sectors');

// Reference: flood sectors within the urban area
var referenceImg = urbanImg.updateMask(sectorsImg.mask()).rename('reference');

// Final classified maps (already clipped to the urban area by script 4)
var methods = [
  {name: 'HAND 3 m', asset: 'imgPosClassificadaSlicedHAND_3m_riscoInundacao', color: 'FFD700'},
  {name: 'HAND 4 m', asset: 'imgPosClassificadaSlicedHAND_4m_riscoInundacao', color: 'FFA500'},
  {name: 'HAND 5 m', asset: 'imgPosClassificadaSlicedHAND_5m_riscoInundacao', color: 'FF4500'},
  {name: 'X-Means',  asset: 'imgPosClassificadaNaoSuperv_riscoInundacao',     color: '9932CC'},
  {name: 'PU (semi-supervised)', asset: 'imgPosClassificadaSemiSuperv_riscoInundacao', color: '00A651'}
];
var imgHAND5m = ee.Image(PATH + methods[2].asset).select('classification_hand');
var imgXMeans = ee.Image(PATH + methods[3].asset).select('cluster');
var imgPU     = ee.Image(PATH + methods[4].asset).select('classification');


// ==================================================================
// 2) FSIVI INDEX
//    Domain: urban area with elevation <= maximum elevation observed
//    within a 200 m buffer around the risk sectors
// ==================================================================
var fsiviBands = ['elevacao', 'distancia', 'declividade',
                  'condutividade_hidraulica_solo', 'hand', 'twi'];

var sectorBuffer200m = setor_risco.geometry().buffer(200, 0);
var elevation = spatialData.select('elevacao');
var maxElevation = ee.Number(elevation.reduceRegion({
  reducer: ee.Reducer.max(),
  geometry: sectorBuffer200m,
  scale: SCALE,
  maxPixels: 1e10
}).get('elevacao'));

var fsiviDomain = elevation.lte(maxElevation)
  .and(spatialData.select('usocobersolo_classification_2023').eq(24));
var predictors = spatialData.select(fsiviBands).updateMask(fsiviDomain);

// Min-max normalization within the domain: x_norm = (x - min) / (max - min)
var minMax = predictors.reduceRegion({
  reducer: ee.Reducer.minMax(),
  scale: SCALE,
  maxPixels: 1e10
});
var normalized = ee.Image.cat(fsiviBands.map(function (b) {
  var vmin = ee.Number(minMax.get(b + '_min'));
  var vmax = ee.Number(minMax.get(b + '_max'));
  return predictors.select(b).subtract(vmin).divide(vmax.subtract(vmin)).rename(b + '_norm');
}));

// Weights = Random Forest importances renormalized to sum to 1
var importances = ee.Feature(ee.FeatureCollection(PATH + 'importancia_atributos_inund').first())
  .toDictionary(fsiviBands);
var importanceSum = ee.Number(importances.values().reduce(ee.Reducer.sum()));
var weights = importances.map(function (k, v) { return ee.Number(v).divide(importanceSum); });
print('FSIVI weights (sum to 1):', weights);

// FSIVI: predictors inversely related to susceptibility enter as (1 - x); TWI enters directly
var fsivi = normalized.expression(
  'wSl*(1-sl) + wEl*(1-el) + wDi*(1-di) + wKs*(1-ks) + wHa*(1-ha) + wTw*tw', {
    sl: normalized.select('declividade_norm'),
    el: normalized.select('elevacao_norm'),
    di: normalized.select('distancia_norm'),
    ks: normalized.select('condutividade_hidraulica_solo_norm'),
    ha: normalized.select('hand_norm'),
    tw: normalized.select('twi_norm'),
    wSl: ee.Number(weights.get('declividade')),
    wEl: ee.Number(weights.get('elevacao')),
    wDi: ee.Number(weights.get('distancia')),
    wKs: ee.Number(weights.get('condutividade_hidraulica_solo')),
    wHa: ee.Number(weights.get('hand')),
    wTw: ee.Number(weights.get('twi'))
  }).rename('suscetibilidade_inundacao');

// 3x3 mean smoothing (morphological mean filter, Fig. 18)
fsivi = fsivi.focal_mean({radius: 1, units: 'pixels', kernel: ee.Kernel.square(1)});

// FSIVI restricted to the area classified as flood-prone by the PU model
var fsiviPU = fsivi.updateMask(imgPU.mask());

// FSIVI descriptive statistics
var statsReducer = ee.Reducer.minMax()
  .combine(ee.Reducer.mean(), '', true)
  .combine(ee.Reducer.stdDev(), '', true)
  .combine(ee.Reducer.variance(), '', true)
  .combine(ee.Reducer.skew(), '', true)
  .combine(ee.Reducer.kurtosis(), '', true)
  .combine(ee.Reducer.percentile([0, 25, 50, 75, 100]), '', true);
print('FSIVI - descriptive statistics:',
      fsivi.reduceRegion({reducer: statsReducer, scale: SCALE, maxPixels: 1e10}));
print('FSIVI - minimum within the PU flood-prone area:',
      fsiviPU.reduceRegion({reducer: ee.Reducer.min(), scale: SCALE, maxPixels: 1e10}));

// Histogram
print(ui.Chart.image.histogram({image: fsivi, region: geometry, scale: SCALE})
  .setOptions({
    title: 'Histogram - FSIVI (Flood Susceptibility Index based on Variable Importance)',
    hAxis: {title: 'Pixel value'},
    vAxis: {title: 'Frequency'},
    series: [{color: 'purple'}]
  }));


// ==================================================================
// 3) TABLE 4 - AREA-LEVEL METRICS
//    Reference (denominator) = flood sectors within the urban area
// ==================================================================
var sectorAreaVector = floodSectors.geometry(1).area(1).divide(1e4);  // official polygon area
var urbanArea        = areaHa(urbanImg);
var fsiviDomainArea  = areaHa(fsivi);
var referenceArea    = areaHa(referenceImg);

print('CPRM/SGB flood sectors, total polygon area (ha):', sectorAreaVector);
print('Urban area (MapBiomas, 10 m) within the study area (ha):', urbanArea);
print('Analysed urban area - FSIVI domain (ha):', fsiviDomainArea);
print('Flood sectors within the urban area - reference (ha):', referenceArea);
print('Urban share of the sectors (%):', referenceArea.divide(sectorAreaVector).multiply(100));

var table4 = ee.FeatureCollection(methods.map(function (m) {
  var predicted = ee.Image(PATH + m.asset).select(0).selfMask().clip(geometry);

  var P = areaHa(predicted);                                     // predicted area
  var I = areaHa(predicted.updateMask(referenceImg.mask()));     // predicted within reference

  return ee.Feature(null, {
    method:              m.name,
    predicted_area_ha:   P,
    inside_ha:           I,
    outside_ha:          P.subtract(I),
    area_recall_pct:     I.divide(referenceArea).multiply(100),
    area_precision_pct:  I.divide(P).multiply(100),
    // Fpb (Li and Guo 2013; Li et al. 2022) = 2 TP / (TP + FN + FP),
    // with TP = I, FN = reference - I and FP = P - I, i.e. 2 I / (reference + P - I)
    Fpb:                 I.multiply(2).divide(referenceArea.add(P).subtract(I)),
    pct_analysed_urban_area: P.divide(fsiviDomainArea).multiply(100),
    // checks: must equal inside_ha and 0, respectively
    check_inside_sectors_ha:  areaHa(predicted.updateMask(sectorsImg.mask())),
    check_outside_domain_ha:  P.subtract(areaHa(predicted.updateMask(fsivi.mask())))
  });
}));
print('Table 4 - area-level metrics', table4);


// ==================================================================
// 4) TABLE 7 - TWO-TIER SUSCEPTIBILITY CLASSES
//    Very high = PU flood-prone area; other classes = FSIVI natural breaks (Jenks)
// ==================================================================
var outsidePU = fsivi.updateMask(imgPU.mask().unmask(0).not());
var fsiviClasses = [
  {name: 'Very low (<0.51)',       img: outsidePU.lt(0.5065).selfMask()},
  {name: 'Low (0.51-0.64)',        img: outsidePU.gte(0.5065).and(outsidePU.lt(0.6351)).selfMask()},
  {name: 'Moderate (0.64-0.75)',   img: outsidePU.gte(0.6351).and(outsidePU.lt(0.7450)).selfMask()},
  {name: 'High (>=0.75)',          img: outsidePU.gte(0.7450).selfMask()},
  {name: 'Very high (PU flood-prone area)', img: fsiviPU}
];
var table7 = ee.FeatureCollection(fsiviClasses.map(function (c) {
  var a = areaHa(c.img);
  return ee.Feature(null, {class_name: c.name, area_ha: a,
                           pct_analysed_urban_area: a.divide(fsiviDomainArea).multiply(100)});
}));
print('Table 7 - susceptibility classes', table7);
print('PU pixels with FSIVI >= 0.745 (%):',
      areaHa(fsiviPU.gte(0.7450).selfMask()).divide(areaHa(fsiviPU)).multiply(100));

// Class raster (1-5) for visualization (Fig. S9)
var classesImg = ee.Image(0)
  .where(outsidePU.lt(0.5065), 1)
  .where(outsidePU.gte(0.5065), 2)
  .where(outsidePU.gte(0.6351), 3)
  .where(outsidePU.gte(0.7450), 4)
  .where(imgPU.mask().unmask(0).and(fsivi.mask()), 5)
  .selfMask().rename('class');
var paletteClasses = ['2C7BB6', 'ABD9E9', 'FFFFBF', 'FDAE61', 'D7191C'];


// ==================================================================
// 5) ATTENTION ZONES (connected components of the PU flood-prone area)
// ==================================================================
var zonesPU = imgPU.connectedComponents({connectedness: ee.Kernel.plus(1), maxSize: 1024});
var highlightRegions = ee.FeatureCollection([
  regioes_atencao_inicioDaInund99, regioes_atencao_inicioDaInund96,
  regioes_atencao_inicioDaInund95, regioes_atencao_inicioDaInund90,
  regioes_atencao_inicioDaInund89, regioes_atencao_inicioDaInund88
]);


// ==================================================================
// 6) ANIMATION (GIF): FSIVI above levels from 99% to 75%
// ==================================================================
var Text = require('users/gena/packages:text');
var gifFrames = ee.ImageCollection(ee.List.sequence(99, 75, -1).map(function (level) {
  level = ee.Number(level);
  var label = Text.draw(ee.String('Risk level ').cat(level.format('%d')).cat('%'),
                        point_text, 10,
                        {fontSize: 32, textColor: 'FFFFFF', outlineColor: '000000', outlineWidth: 2});
  return fsivi.gte(level.divide(100)).clip(geometry_forgif)
    .focal_mean({radius: 1, units: 'pixels', kernel: ee.Kernel.square(1)})
    .visualize({palette: paletteFSIVI}).blend(label);
}));
print('Animation preview', ui.Thumbnail(gifFrames,
      {dimensions: 512, region: geometry_forgif, framesPerSecond: 1, format: 'gif'}));


// ==================================================================
// 7) SAMPLES FOR THE SEPARABILITY ANALYSIS (Python)
// ==================================================================
var separabilityBuffer = setor_risco.geometry().buffer(1700, 0);  // reduce to shrink the sampled area
var separabilitySamples = spatialData.select(fsiviBands)
  .addBands(imgPU.unmask(0))
  .addBands(imgXMeans.unmask(0))
  .addBands(imgHAND5m.unmask(0))
  .clip(separabilityBuffer)
  .sample({region: separabilityBuffer, scale: SCALE, geometries: true});
print('Number of separability samples:', separabilitySamples.size());


// ==================================================================
// 8) EXPORTS (run from the Tasks tab)
// ==================================================================
Export.table.toDrive({collection: table4, description: 'Table4_area_metrics',
                      folder: FOLDER, fileFormat: 'CSV'});
Export.table.toDrive({collection: table7, description: 'Table7_susceptibility_classes',
                      folder: FOLDER, fileFormat: 'CSV'});
Export.table.toDrive({collection: separabilitySamples, description: 'dadosAvaliacaoSeparabilidade',
                      folder: FOLDER});
Export.table.toDrive({collection: highlightRegions, description: 'regioes_de_destaques',
                      folder: FOLDER});

var exportImage = function (img, name) {
  Export.image.toAsset({image: img, description: name, assetId: PATH + name,
                        region: geometry_forgif, scale: SCALE, maxPixels: 1e10});
  Export.image.toDrive({image: img, description: name, folder: FOLDER,
                        region: geometry_forgif, scale: SCALE, maxPixels: 1e10});
};
exportImage(fsivi,   'Mapa_calor_de_risco_inundacao_posClassif');
exportImage(fsiviPU, 'Mapa_calor_sobre_risco_inundacao_masked_posClassif');
exportImage(zonesPU.randomVisualizer().toInt8(), 'Zonas_risco_inun_posClassif');

Export.video.toDrive({collection: gifFrames, description: 'video_riscoinduncacao_PGM',
                      fileNamePrefix: 'riscoInundacao_animation', framesPerSecond: 1,
                      region: geometry_forgif, dimensions: 1024, folder: FOLDER});


// ==================================================================
// 9) VISUALIZATION
// ==================================================================
Map.centerObject(floodSectors, 14);
Map.addLayer(urbanImg,     {palette: ['999999'], opacity: 0.5}, '1) Urban area (MapBiomas 24)');
Map.addLayer(sectorsImg,   {palette: ['0000FF'], opacity: 0.4}, '2) Flood sectors (raster)', false);
Map.addLayer(referenceImg, {palette: ['FF0000']},               '3) Reference: sectors within urban area');
methods.forEach(function (m) {
  Map.addLayer(ee.Image(PATH + m.asset).select(0).selfMask(),
               {palette: [m.color], opacity: 0.7}, '4) ' + m.name, m.name.indexOf('PU') === 0);
});
Map.addLayer(fsivi,      visFSIVI, '5) FSIVI', false);
Map.addLayer(fsiviPU,    visFSIVI, '6) FSIVI over the PU flood-prone area', false);
Map.addLayer(classesImg, {min: 1, max: 5, palette: paletteClasses}, '7) Susceptibility classes (Table 7)', false);
Map.addLayer(zonesPU.randomVisualizer(), {}, '8) Attention zones (PU components)', false);
Map.addLayer(highlightRegions.style({color: '000000', fillColor: '00000000', width: 2}), {}, '9) Highlighted regions', false);
Map.addLayer(floodSectors.style({color: '0000FF', fillColor: '00000000', width: 2}), {}, '10) CPRM/SGB sector outlines');
