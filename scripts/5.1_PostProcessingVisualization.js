/***************************************************************
 * PROJECT: Urban Flood Susceptibility Mapping
 * PLATFORM: Google Earth Engine (JavaScript)
 * AUTHOR: Gilberto Junior
 * DESCRIPTION:
 *  - Computation of flood risk areas in urban regions
 *  - Evaluation of classifications (unsupervised, semi-supervised and HAND)
 *  - Generation of flood susceptibility map
 *  - Export of results (tables, images and GIF)
 ***************************************************************/

//Area calculation function (in hectares)
var areaCalculate = function(img,geom){
      //The input image is multiplied by an image.pixelArea
      //image.pixelArea holds the value where each pixel is the area of that pixel in square meters.
      var areaImg = img.multiply(ee.Image.pixelArea());

      //Sums the multiplied image of the resulting image area within the specified geometry (geom).
      //This is done using an Earth Engine reducer ee.Reducer.sum().
      var area = areaImg.reduceRegion({
        reducer: ee.Reducer.sum(),
        geometry: geom,
        maxPixels: 1e11,
        scale:10
      })

      //Converts the summed value into hectares and rounds to drop the digits after the decimal point
      var areaValue = ee.Number(area.values().get(0)).divide(10000)

      //print("Area in hectares:",areaValue)
      return areaValue
    }

//Land use and land cover mask
var spatialData = ee.Image('.../assets/ProjetoEnchente/raster_dados_espaciais_inundacao')
var landCover = spatialData.select('usocobersolo_classification_2023')
var uniqueClassValuesYears = ee.List([24]) //urban area class (24), Wetland and Marsh Area, Rivers and Lakes and Ocean
//print(uniqueClassValuesYears)
var landCoverMask = landCover.remap(uniqueClassValuesYears, uniqueClassValuesYears)
landCoverMask = landCover.updateMask(landCoverMask)
//Map.addLayer(landCoverMask,{},'Land use and land cover mask',false)
landCoverMask = landCoverMask.gt(0).selfMask().unmask(0).rename('setor_risco')
//Map.addLayer(landCoverMask,{},"Land use and cover mask",false)

var floodRiskSector = setor_risco.filter(ee.Filter.eq('tipolo_g1', 'Inundação'))
var imgAreaFloodRiskSector = ee.Image(1).rename("setor_risco").reproject({
  crs: 'EPSG:4326',
  scale: 10
}).clip(floodRiskSector)
//print(imgAreaFloodRiskSector)
//Map.addLayer(imgAreaFloodRiskSector)

var imgAreaFloodRiskSectorLandCover = imgAreaFloodRiskSector.add(landCoverMask)
imgAreaFloodRiskSectorLandCover = imgAreaFloodRiskSectorLandCover.gte(2).selfMask()
//Map.addLayer(imgAreaFloodRiskSectorLandCover,{bands: ["setor_risco"],opacity: 1, palette: ["ff1f12"]},'flood sector in urban region',false)

// (removed) manual adjustment polygon — Table 4 is computed without any manual blending
//Map.addLayer(adjustImgForAreaCalc)

imgAreaFloodRiskSectorLandCover = imgAreaFloodRiskSectorLandCover /* adjustment polygon removed: area metrics computed strictly against the CPRM/SGB sectors */
//Map.addLayer(imgAreaFloodRiskSectorLandCover)

var areaFloodRiskSector = areaCalculate(imgAreaFloodRiskSectorLandCover,floodRiskSector)
print("Area of risk sectors in urban regions", areaFloodRiskSector)

var clusteredImageFloodRisk = ee.Image('.../assets/ProjetoEnchente/imgPosClassificadaNaoSuperv_riscoInundacao')
Map.addLayer(clusteredImageFloodRisk,{},'clusteredImageFloodRisk')
var clusteredImageFloodRiskFilled = clusteredImageFloodRisk /* adjustment polygon removed: area metrics computed strictly against the CPRM/SGB sectors */;
var clusteredImageFloodRiskArea = clusteredImageFloodRiskFilled
.select("cluster").reproject({
  crs: 'EPSG:4326',
  scale: 10
}).clip(floodRiskSector)
var areaClusteredFloodRiskSector = areaCalculate(clusteredImageFloodRiskArea,floodRiskSector)
print('Unsupervised classified area (clustered) over the risk sectors:', areaClusteredFloodRiskSector)

var classifiedImageFloodRisk = ee.Image('.../assets/ProjetoEnchente/imgPosClassificadaSemiSuperv_riscoInundacao')
var classifiedImageFloodRiskFilled = classifiedImageFloodRisk /* adjustment polygon removed: area metrics computed strictly against the CPRM/SGB sectors */;
var classifiedImageFloodRiskArea = classifiedImageFloodRiskFilled
.select("classification").reproject({
  crs: 'EPSG:4326',
  scale: 10
}).clip(floodRiskSector)
//Map.addLayer(classifiedImageFloodRiskArea,{},'classifiedImageFloodRisk')
var areaClassifiedFloodRiskSector = areaCalculate(classifiedImageFloodRiskArea,floodRiskSector)
print('Semi-supervised classified area over the risk sectors:',areaClassifiedFloodRiskSector)


var classifiedImageHAND3mFloodRisk = ee.Image('.../assets/ProjetoEnchente/imgPosClassificadaSlicedHAND_3m_riscoInundacao')
var classifiedImageHAND3mFloodRiskFilled = classifiedImageHAND3mFloodRisk /* adjustment polygon removed: area metrics computed strictly against the CPRM/SGB sectors */;
var classifiedImageHAND3mFloodRiskArea = classifiedImageHAND3mFloodRiskFilled
.select("classification_hand").reproject({
  crs: 'EPSG:4326',
  scale: 10
}).clip(floodRiskSector)
var areaClassifiedHAND3mFloodRiskSector = areaCalculate(classifiedImageHAND3mFloodRiskArea,floodRiskSector)
print('Sliced classified area (HAND 3 meters) over the risk sectors:', areaClassifiedHAND3mFloodRiskSector)

var classifiedImageHAND4mFloodRisk = ee.Image('.../assets/ProjetoEnchente/imgPosClassificadaSlicedHAND_4m_riscoInundacao')
var classifiedImageHAND4mFloodRiskFilled = classifiedImageHAND4mFloodRisk /* adjustment polygon removed: area metrics computed strictly against the CPRM/SGB sectors */;
var classifiedImageHAND4mFloodRiskArea = classifiedImageHAND4mFloodRiskFilled
.select("classification_hand").reproject({
  crs: 'EPSG:4326',
  scale: 10
}).clip(floodRiskSector)
var areaClassifiedHAND4mFloodRiskSector = areaCalculate(classifiedImageHAND4mFloodRiskArea,floodRiskSector)
print('Sliced classified area (HAND 4 meters) over the risk sectors:', areaClassifiedHAND4mFloodRiskSector)

var classifiedImageHAND5mFloodRisk = ee.Image('.../assets/ProjetoEnchente/imgPosClassificadaSlicedHAND_5m_riscoInundacao')
Map.addLayer(classifiedImageHAND5mFloodRisk,{},'classifiedImageHAND5mFloodRisk')
var classifiedImageHAND5mFloodRiskFilled = classifiedImageHAND5mFloodRisk /* adjustment polygon removed: area metrics computed strictly against the CPRM/SGB sectors */;
var classifiedImageHAND5mFloodRiskArea = classifiedImageHAND5mFloodRiskFilled
.select("classification_hand").reproject({
  crs: 'EPSG:4326',
  scale: 10
}).clip(floodRiskSector)
var areaClassifiedHAND5mFloodRiskSector = areaCalculate(classifiedImageHAND5mFloodRiskArea,floodRiskSector)
print('Sliced classified area (HAND 5 meters) over the risk sectors:', areaClassifiedHAND5mFloodRiskSector)


var percentClassificationHAND_3m = (areaClassifiedHAND3mFloodRiskSector.divide(areaFloodRiskSector)).multiply(100)
print("Accuracy percentage of the sliced classification (HAND 3 meters) over the CPRM Flood region",percentClassificationHAND_3m)
var percentClassificationHAND_4m = (areaClassifiedHAND4mFloodRiskSector.divide(areaFloodRiskSector)).multiply(100)
print("Accuracy percentage of the sliced classification (HAND 4 meters) over the CPRM Flood region",percentClassificationHAND_4m)
var percentClassificationHAND_5m = (areaClassifiedHAND5mFloodRiskSector.divide(areaFloodRiskSector)).multiply(100)
print("Accuracy percentage of the sliced classification (HAND 5 meters) over the CPRM Flood region",percentClassificationHAND_5m)

var percentCluster = (areaClusteredFloodRiskSector.divide(areaFloodRiskSector)).multiply(100)
print("Accuracy percentage of the unsupervised classification (clustering) over the CPRM Flood region",percentCluster)
var percentClassification = (areaClassifiedFloodRiskSector.divide(areaFloodRiskSector)).multiply(100)
print("Accuracy percentage of the semi-supervised classification (randforest) over the CPRM Flood region",percentClassification)

//Export data to identify class separability in Python.
var riskSectorGeometryBuffer1000 = setor_risco.geometry().buffer(1700,0)// to make the classification area smaller, just decrease this buffer value
//Map.addLayer(riskSectorGeometryBuffer1000,{},"setor_risco_Inundacao_CRPM 1000m buffer",false)

var spatialDataWithClassifications = spatialData.addBands(clusteredImageFloodRisk.select('cluster').unmask(0))
spatialDataWithClassifications = spatialDataWithClassifications.addBands(classifiedImageHAND5mFloodRisk.select('classification_hand').unmask(0))
spatialDataWithClassifications = spatialDataWithClassifications.addBands(classifiedImageFloodRisk.select('classification').unmask(0))

var bandsSeparabilityEval  = ['elevacao', 'distancia', 'declividade', 'condutividade_hidraulica_solo','hand','twi','classification','cluster','classification_hand']
spatialDataWithClassifications = spatialDataWithClassifications.select(bandsSeparabilityEval).clip(riskSectorGeometryBuffer1000)
//Map.addLayer(spatialDataWithClassifications)

var separabilityEvalData = spatialDataWithClassifications.sample({
  //numPixels: 4000,
  region: riskSectorGeometryBuffer1000,
  scale: 10,
  geometries: true
});

Export.table.toDrive({
		collection: separabilityEvalData,
	  description: "dadosAvaliacaoSeparabilidade",
	  folder:"projetoEnchenteAssets",
})

// Display in the console
//Map.addLayer(separabilityEvalData, {color: 'blue'}, 'Sample pixel points',false)
print('Number of separability samples',separabilityEvalData.size())

//---------------

var floodSectorsPostClassif = classifiedImageFloodRisk.select('classification').connectedComponents({
  connectedness: ee.Kernel.plus(1),
  maxSize: 1024//128
});
//print(floodSectorsPostClassif)

//----------------

//Risk heat map
var riskSectorGeometryBuffer = setor_risco.geometry().buffer(200,0)
//Map.addLayer(riskSectorGeometryBuffer,{},"setor_risco_Inundacao_CRPM 200m buffer",false)

var spatialData = ee.Image('.../assets/ProjetoEnchente/raster_dados_espaciais_inundacao')
//print(spatialData)
var bands  = ['elevacao', 'distancia', 'declividade', 'condutividade_hidraulica_solo','hand','twi','usocobersolo_classification_2023']
var elevation = spatialData.select(['elevacao'])

// Reduces the image within the buffer region to find the maximum value
var maxElevation = elevation.reduceRegion({
  reducer: ee.Reducer.max(),
  geometry: riskSectorGeometryBuffer,
  scale: 10,  // adjust according to your raster resolution
  maxPixels: 1e10
});

// Prints the maximum value in the console
var maxElevation_value = maxElevation.get('elevacao').getInfo()
//print('Maximum elevation value in the buffer:', maxElevation_value)

var mask = elevation.lte(maxElevation_value)  // lte = less than or equal

// Step 3: Applies the mask to the elevation image
var maskedElevation = elevation.updateMask(mask)

//Map.addLayer(maskedElevation, {min: 0, max: maxElevation_value, palette: ['blue', 'green', 'yellow']}, 'Masked elevation <= maximum value')

var landCoverUse = spatialData.select(['usocobersolo_classification_2023']).eq(24)

var maskedElevationFinal = maskedElevation.updateMask(landCoverUse);

//Map.addLayer(maskedElevationFinal, {min: 0, max: maxElevation_value, palette: ['blue', 'green', 'yellow']},  'Masked elevation + land use = 24');

var spatialDataBandsOfInterest = spatialData.select([
  'elevacao',
  'distancia',
  'declividade',
  'condutividade_hidraulica_solo',
  'hand',
  'twi'
]);

// Applies the final mask (of elevation + land use) to all these bands
var imgSpatialDataBandsOfInterest = spatialDataBandsOfInterest.updateMask(maskedElevationFinal.mask());

// Visualizes (for example, the 'distancia' band)
//Map.addLayer(imgSpatialDataBandsOfInterest,{},"Selected bands")
//print(imgSpatialDataBandsOfInterest)

/*
elevacao_norm      = (elevacao - minElev) / (maxElev - minElev);
dist_rio_norm      = (dist_rio - minDist) / (maxDist - minDist);
declividade_norm   = (declividade - minDecliv) / (maxDecliv - minDecliv);
condutividade_norm = (condutividade - minCondut) / (maxCondut - minCondut);
hand_norm = (hand - minHand) / (maxHand - minHand);
twi_norm = (twi - minTwi) / (maxTwi - minTwi);
*/

// Computes the min and max values of each band within the buffer
var stats = imgSpatialDataBandsOfInterest.reduceRegion({
  reducer: ee.Reducer.minMax(),
  scale: 10,
  maxPixels: 1e10
});
//print(stats)

// Extracts the numeric values
var minElev   = ee.Number(stats.get('elevacao_min'));
var maxElev   = ee.Number(stats.get('elevacao_max'));
var minDist   = ee.Number(stats.get('distancia_min'));
var maxDist   = ee.Number(stats.get('distancia_max'));
var minDecliv = ee.Number(stats.get('declividade_min'));
var maxDecliv = ee.Number(stats.get('declividade_max'));
var minCondut = ee.Number(stats.get('condutividade_hidraulica_solo_min'));
var maxCondut = ee.Number(stats.get('condutividade_hidraulica_solo_max'));
var minHand = ee.Number(stats.get('hand_min'));
var maxHand = ee.Number(stats.get('hand_max'));
var minTwi = ee.Number(stats.get('twi_min'));
var maxTwi = ee.Number(stats.get('twi_max'));

// Normalizations using .expression()
var elevationNorm = imgSpatialDataBandsOfInterest.expression(
  '(e - minE) / (maxE - minE)', {
    'e': imgSpatialDataBandsOfInterest.select('elevacao'),
    'minE': minElev,
    'maxE': maxElev
  }).rename('elevacao_norm');

var distanceNorm = imgSpatialDataBandsOfInterest.expression(
  '(d - minD) / (maxD - minD)', {
    'd': imgSpatialDataBandsOfInterest.select('distancia'),
    'minD': minDist,
    'maxD': maxDist
  }).rename('distancia_norm');

var slopeNorm = imgSpatialDataBandsOfInterest.expression(
  '(s - minS) / (maxS - minS)', {
    's': imgSpatialDataBandsOfInterest.select('declividade'),
    'minS': minDecliv,
    'maxS': maxDecliv
  }).rename('declividade_norm');

var conductivityNorm =imgSpatialDataBandsOfInterest.expression(
  '(c - minC) / (maxC - minC)', {
    'c': imgSpatialDataBandsOfInterest.select('condutividade_hidraulica_solo'),
    'minC': minCondut,
    'maxC': maxCondut
  }).rename('condutividade_norm');

var handNorm =imgSpatialDataBandsOfInterest.expression(
  '(h - minH) / (maxH - minH)', {
    'h': imgSpatialDataBandsOfInterest.select('hand'),
    'minH': minHand,
    'maxH': maxHand
  }).rename('hand_norm');

var twiNorm =imgSpatialDataBandsOfInterest.expression(
  '(t - minT) / (maxT - minT)', {
    't': imgSpatialDataBandsOfInterest.select('twi'),
    'minT': minTwi,
    'maxT': maxTwi
  }).rename('twi_norm');

// Joins all the normalized bands
var normalizedImage = elevationNorm
  .addBands(distanceNorm)
  .addBands(slopeNorm)
  .addBands(conductivityNorm)
  .addBands(handNorm)
  .addBands(twiNorm);

var weights = ee.FeatureCollection('.../assets/ProjetoEnchente/importancia_atributos_inund')
var props = ee.Feature(weights.first()).toDictionary();
//print('All properties:', props);

var import_slope =  ee.Number(props.get('declividade'))
var import_elevation =  ee.Number(props.get('elevacao'))
var import_distance=  ee.Number(props.get('distancia'))
var import_conductivity =  ee.Number(props.get('condutividade_hidraulica_solo'))
var import_hand =  ee.Number(props.get('hand'))
var import_twi =  ee.Number(props.get('twi'))

var weightsSum = import_conductivity.add(import_slope).add(import_distance).add(import_elevation).add(import_hand).add(import_twi)
//print(weightsSum)

var weight_slope = import_slope.divide(weightsSum)
var weight_elevation = import_elevation.divide(weightsSum)
var weight_distance = import_distance.divide(weightsSum)
var weight_conductivity_hydraulic_soil = import_conductivity.divide(weightsSum)
var weight_hand = import_hand.divide(weightsSum)
var weight_twi = import_twi.divide(weightsSum)
print("Feature weights: (weight_slope,weight_elevation,weight_distance,weight_conductivity_hydraulic_soil,weight_hand,weight_twi) ", weight_slope,weight_elevation,weight_distance,weight_conductivity_hydraulic_soil,weight_hand,weight_twi)

var floodRiskImg = normalizedImage.expression(
  'weight_sl * (1 - sl) + weight_el * (1 - el) + weight_di * (1 - di) + weight_co * (1 - co) + weight_ha * (1 - ha) + weight_tw * (tw)', {
    'sl': normalizedImage.select('declividade_norm'),
    'el': normalizedImage.select('elevacao_norm'),
    'di': normalizedImage.select('distancia_norm'),
    'co': normalizedImage.select('condutividade_norm'),
    'ha': normalizedImage.select('hand_norm'),
    'tw': normalizedImage.select('twi_norm'),
    'weight_sl': weight_slope,
    'weight_el': weight_elevation,
    'weight_di': weight_distance,
    'weight_co': weight_conductivity_hydraulic_soil,
    'weight_ha': weight_hand,
    'weight_tw': weight_twi,
  }).rename('suscetibilidade_inundacao');

//{min: 0.34, max: 0.96, palette: ['#1a9850', '#fee08b', '#d73027']}
//Map.addLayer(floodRiskImg,imageVisParam2,"Heat Map - Flood Risk")
floodRiskImg = floodRiskImg.focal_mean({radius: 1, units: 'pixels', kernel: ee.Kernel.square(1)})

var imageVisParam3 ={ bands: ["suscetibilidade_inundacao"],
max: 0.9534484538232613,
min: 0.3699895127314622,
opacity: 1,
palette: ["22dd0e","f9fe31","d70c0c"]}

Map.addLayer(floodRiskImg,imageVisParam3,"Heat Map - Flood Risk (smoothed by mean)")

Map.addLayer(floodSectorsPostClassif.randomVisualizer(), null, 'Risk Zones');
//Map.addLayer(floodRiskImg.gte(0.83),imageVisParam2,"Heat Map - Flood Risk level 83%")

var riskMask = classifiedImageFloodRisk.select('classification');
riskMask = riskMask.updateMask(riskMask.mask());
var floodRiskImgMasked = floodRiskImg.select('suscetibilidade_inundacao').updateMask(riskMask);
Map.addLayer(floodRiskImgMasked,imageVisParam3,"Heat Map over Flood Risk")

// Computes statistics over the generated image
var minmaxFloodRiskImg = floodRiskImg.reduceRegion({
  reducer: ee.Reducer.minMax(),
  scale: 10,
  maxPixels: 1e10
});
print("minmaxFloodRiskImg",minmaxFloodRiskImg)

var meanFloodRiskImg = floodRiskImg.reduceRegion({
  reducer: ee.Reducer.mean(),
  scale: 10,
  maxPixels: 1e10
});
print("meanFloodRiskImg",meanFloodRiskImg)

var medianFloodRiskImg = floodRiskImg.reduceRegion({
  reducer: ee.Reducer.median(),
  scale: 10,
  maxPixels: 1e10
});
print("medianFloodRiskImg",medianFloodRiskImg)

var stdDevFloodRiskImg = floodRiskImg.reduceRegion({
  reducer: ee.Reducer.stdDev(),
  scale: 10,
  maxPixels: 1e10
});
print("stdDevFloodRiskImg",stdDevFloodRiskImg)

var varianceFloodRiskImg = floodRiskImg.reduceRegion({
  reducer: ee.Reducer.variance(),
  scale: 10,
  maxPixels: 1e10
});
print("varianceFloodRiskImg",varianceFloodRiskImg)

var kurtosisFloodRiskImg = floodRiskImg.reduceRegion({
  reducer: ee.Reducer.kurtosis(),
  scale: 10,
  maxPixels: 1e10
});
print("kurtosisFloodRiskImg",kurtosisFloodRiskImg)

var skewFloodRiskImg = floodRiskImg.reduceRegion({
  reducer: ee.Reducer.skew(),
  scale: 10,
  maxPixels: 1e10
});
print("skewFloodRiskImg",skewFloodRiskImg)

var percentileFloodRiskImg = floodRiskImg.reduceRegion({
  reducer: ee.Reducer.percentile([0, 25, 50,75, 100]),
  scale: 10,
  maxPixels: 1e10
});
print("percentileFloodRiskImg",percentileFloodRiskImg)

Map.addLayer(floodRiskSector,{},"CPRM risk sectors")

// 5. Display the histogram in the console
var hist = ui.Chart.image.histogram({
  //image: floodRiskImgMasked,//
  image: floodRiskImg,
  region: geometry,
  scale: 10,  // spatial resolution
  //minBucketWidth: 10  // minimum histogram bucket width
}).setOptions({
  title: 'Histogram - FSIVI (Flood Susceptibility Index based on Variable Importance)',
  hAxis: {title: 'Pixel value'},
  vAxis: {title: 'Frequency'},
  series: [{color: 'purple'}]
});
print(hist);

// Import the geetools text library
var Text = require('users/gena/packages:text');
// List of levels from 97 down to 83
var levels = ee.List.sequence(99, 75, -1);
// Uses iterate to build the list of images
var image_forGif_list = levels.iterate(function(level, list) {
  level = ee.Number(level);
  var label = ee.String('Risk level ')
  .cat(level.format('%d'))
  .cat('%');

  list = ee.List(list);
  var level_prob = level.divide(100);
  var image_forGif = floodRiskImg.gte(level_prob).clip(geometry_forgif).focal_mean({radius: 1, units: 'pixels', kernel: ee.Kernel.square(1)});
  //var image_forGif = floodRiskImgMasked.gte(level_prob).clip(geometry_forgif).focal_mean({radius: 1, units: 'pixels', kernel: ee.Kernel.square(1)});

  var text = Text.draw(label, point_text, 10, {
    fontSize: 32,
    textColor: 'FFFFFF',
    outlineColor: '000000',
    outlineWidth: 2
  });
  var image_forGif_text = image_forGif.visualize({
    palette: ["22dd0e", "f9fe31", "d70c0c"]
  }).blend(text);
  return list.add(image_forGif_text);
}, ee.List([]));
// Converts the result into an ImageCollection
image_forGif_list = ee.List(image_forGif_list);
var collection_imgs = ee.ImageCollection(image_forGif_list);
print(collection_imgs);
//Map.addLayer(collection_imgs.first(), {}, 'First image with text');

var videoArgs = {
  dimensions: 1024,
  region: geometry_forgif,
  framesPerSecond: 1,
  format: 'gif',
  min: 0.3699895127314622,
  max: 0.9534484538232613,
  palette: ["22dd0e","f9fe31","d70c0c"]
};
//low-resolution preview
print(ui.Thumbnail(collection_imgs))//, videoArgs));

// Export as video
Export.video.toDrive({
  collection: collection_imgs,
  description: 'video_riscoinduncacao_PGM',
  fileNamePrefix: 'riscoInundacao_animation',
  framesPerSecond: 1,
  region: geometry_forgif,
  dimensions: 1024,
  folder:"projetoEnchenteAssets",
});

var assetPathEnchente = '.../assets/ProjetoEnchente/';

Export.image.toAsset({
      image:floodRiskImg,
      description:"Mapa_calor_de_risco_inundacao_posClassif",
      assetId:assetPathEnchente+"Mapa_calor_de_risco_inundacao_posClassif",
      region:geometry_forgif,
      scale:10,
      maxPixels:1e10,
})
Export.image.toDrive({
  image: floodRiskImg,
  description: 'Mapa_calor_de_risco_inundacao_posClassif',
  folder:"projetoEnchenteAssets",
  region: geometry_forgif,
  scale: 10,
  maxPixels: 1e10
});

Export.image.toAsset({
      image:floodRiskImgMasked,
      description:"Mapa_calor_sobre_risco_inundacao_masked_posClassif",//Heat Map over Flood Risk
      assetId:assetPathEnchente+"Mapa_calor_sobre_risco_inundacao_masked_posClassif",
      region:geometry_forgif,
      scale:10,
      maxPixels:1e10,
})
Export.image.toDrive({
  image: floodRiskImgMasked,
  description: 'Mapa_calor_sobre_risco_inundacao_masked_posClassif',
  folder:"projetoEnchenteAssets",
  region: geometry_forgif,
  scale: 10,
  maxPixels: 1e10
});

Export.image.toAsset({
      image:floodSectorsPostClassif.randomVisualizer(),
      description:"Zonas_risco_inun_posClassif",
      assetId:assetPathEnchente+"Zonas_risco_inun_posClassif",
      region:geometry_forgif,
      scale:10,
      maxPixels:1e10,
})
print(floodSectorsPostClassif.randomVisualizer().toInt8())
Export.image.toDrive({
  image: floodSectorsPostClassif.randomVisualizer().toInt8(),
  description: 'Zonas_risco_inun_posClassif',
  folder:"projetoEnchenteAssets",
  region: geometry_forgif,
  scale: 10,
  maxPixels: 1e10
});

var highlightRegions = ee.FeatureCollection([
regioes_atencao_inicioDaInund99,
regioes_atencao_inicioDaInund96,
regioes_atencao_inicioDaInund95,
regioes_atencao_inicioDaInund90,
regioes_atencao_inicioDaInund89,
regioes_atencao_inicioDaInund88
])
Map.addLayer(highlightRegions,{},"highlightRegions")
Export.table.toDrive({
  collection: highlightRegions,
  description: 'regioes_de_destaques',
  folder:"projetoEnchenteAssets",
});
