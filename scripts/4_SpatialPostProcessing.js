// =============================================================================
// Crossing with urban area (class 24) and post-processing for 3 outputs:
// 1) RF (semi-supervised)   2) K-means (unsupervised)   3) HAND (5m,4m,3m)
// =============================================================================

var spatialData = ee.Image('.../assets/ProjetoEnchente/raster_dados_espaciais_inundacao')
var region = spatialData.select(['distancia']).geometry(0)

var classifiedImageRF = ee.Image('.../assets/ProjetoEnchente/img_ClassificadaSemiSuperv_risco_inund')
var clusteredImageKmeans = ee.Image('.../assets/ProjetoEnchente/img_ClassificadaNaoSuperv_risco_inund')
var classifiedImageSlicedHAND_5m = ee.Image('.../assets/ProjetoEnchente/img_ClassificadaSliced_risco_inund_alt5m')
var classifiedImageSlicedHAND_4m = ee.Image('.../assets/ProjetoEnchente/img_ClassificadaSliced_risco_inund_alt4m')
var classifiedImageSlicedHAND_3m = ee.Image('.../assets/ProjetoEnchente/img_ClassificadaSliced_risco_inund_alt3m')

// Land use and land cover mask (selects only urban areas - class 24)
var landCover = spatialData.select('usocobersolo_classification_2023')
var uniqueClassValuesYears = ee.List([24]) //urban area class (24)
var landCoverMask = landCover.remap(uniqueClassValuesYears, uniqueClassValuesYears)
landCoverMask = landCover.updateMask(landCoverMask)
//Map.addLayer(landCoverMask,{},'Land use and land cover mask',false)
landCoverMask = landCoverMask.gt(0).selfMask().unmask(0).rename('classification')
//Map.addLayer(landCoverMask,{},"Land use and cover mask",false)

// ---- Crossing the supervised classification (RF) with the urban mask ----
var classifiedImgLandCover = classifiedImageRF.add(landCoverMask)
classifiedImgLandCover = classifiedImgLandCover.gte(2).selfMask()
Map.addLayer(classifiedImgLandCover,{bands: ["classification"],opacity: 1, palette: ["ff1f12"]},'Classified img crossed with LandCover',false)
//------

// ---- Crossing the clustering (K-means) with the urban mask ----
// Function to get the cluster ID corresponding to the reference point
var getClusterId = function(clusterizedImage,point) {
    var ID = clusterizedImage.reduceRegion({
    reducer:ee.Reducer.mean(),
    geometry:point,
    scale:10
    });
    ID = ID.get('cluster');
    return ee.Number.parse(ID);
}
var riskClusterId = getClusterId(clusteredImageKmeans,point_Cluster);
//print("riskClusterId",riskClusterId)
landCoverMask = landCoverMask.rename('cluster')
var clusteredImageLandCover = clusteredImageKmeans.eq(riskClusterId.getInfo()).add(landCoverMask)
clusteredImageLandCover = clusteredImageLandCover.gte(2).selfMask()
Map.addLayer(clusteredImageLandCover,{bands: ["cluster"],opacity: 1, palette: ["ff1f12"]},'Clustered img crossed with LandCover',false)
//------

// ---- Crossing the HAND classification (5 m) with the urban mask ----
var classifiedImageHAND_smooth_5m = classifiedImageSlicedHAND_5m.gte(-9999).clip(region)
//Map.addLayer(classifiedImageHAND_smooth)
var classifiedImgHAND_LandCover_5m = classifiedImageHAND_smooth_5m.add(landCoverMask).gte(2).selfMask()
//classifiedImgHAND_LandCover = classifiedImgHAND_LandCover_5m.gte(2).selfMask()
Map.addLayer(classifiedImgHAND_LandCover_5m,{bands: ["classification_hand"],opacity: 1, palette: ["ff1f12"]},'Classified HAND img 5m crossed with LandCover',false)
// ---- Crossing the HAND classification (4 m) with the urban mask ----
var classifiedImageHAND_smooth_4m = classifiedImageSlicedHAND_4m.gte(-9999).clip(region)
var classifiedImgHAND_LandCover_4m = classifiedImageHAND_smooth_4m.add(landCoverMask).gte(2).selfMask()
Map.addLayer(classifiedImgHAND_LandCover_4m,{bands: ["classification_hand"],opacity: 1, palette: ["ff1f12"]},'Classified HAND img 4m crossed with LandCover',false)
// ---- Crossing the HAND classification (3 m) with the urban mask ----
var classifiedImageHAND_smooth_3m = classifiedImageSlicedHAND_3m.gte(-9999).clip(region)
var classifiedImgHAND_LandCover_3m = classifiedImageHAND_smooth_3m.add(landCoverMask).gte(2).selfMask()
Map.addLayer(classifiedImgHAND_LandCover_3m,{bands: ["classification_hand"],opacity: 1, palette: ["ff1f12"]},'Classified HAND img 3m crossed with LandCover',false)
//------

//Computes objects by connectivity, area per object (m2), applies a minimum threshold
//and adds visualization layers to the map.
function hotspotsByArea(binaryImg, layerLabelPrefix, minArea_m2, eightConnected, maxSizePx) {
  var _max = maxSizePx || 1024;
  var connKernel = ee.Kernel.plus(1); // 4-connected (cross)

  // 1) Labeling by connectivity
  var labeled = binaryImg.connectedComponents({
    connectedness: connKernel,
    maxSize: _max
  });

  // 2) Number of pixels per object
  var nPixels = labeled.select('labels').connectedPixelCount({
    maxSize: _max,
    eightConnected: !!eightConnected // false -> 4-connected; true -> 8-connected
  });

  // 3) Area per object (m2)
  var area = nPixels.multiply(ee.Image.pixelArea());

  // 4) Mask by minimum area and final hotspots
  var areaMask = area.gte(minArea_m2);
  var hotspots = labeled.updateMask(areaMask);

  // 5) Visualizations (same style as your original code)
  Map.addLayer(labeled.randomVisualizer(), {}, layerLabelPrefix + ' - Objects', false);
  Map.addLayer(nPixels, { min: 1, max: _max }, layerLabelPrefix + ' - Number of pixels', false);
  Map.addLayer(area, { min: 0, max: 3e6, palette: ['0000FF', 'FF00FF'] }, layerLabelPrefix + ' - Area (m2)', false);
  Map.addLayer(hotspots, {}, layerLabelPrefix + ' - Hotspots (>= ' + minArea_m2 + ' m2)', true);

  return { labeled: labeled, nPixels: nPixels, area: area, hotspots: hotspots };
}

// =============================================================================
// Apply the function to the three images (RF, K-means, HAND <= 5 m)
// =============================================================================

// Area threshold: 3,000 m2 | connectivity 4 (as in your snippet) | maxSize 1024
var AREA_MIN_M2 = 3000;
var EIGHT_CON = false;
var MAXSIZE = 1024;

// 1) Classified Image (RF) AND Urban
var img_ClassifiedRF_HotSpot = hotspotsByArea(
  classifiedImgLandCover,          // binary selfMask image
  'Classified (RF) - Hotspots',
  AREA_MIN_M2,
  EIGHT_CON,
  MAXSIZE
);

// 2) Clustered Image (K-means) AND Urban
var img_ClassifiedKMeans_HotSpot = hotspotsByArea(
  clusteredImageLandCover,       // binary selfMask image
  'Clustered (K-means) - Hotspots',
  AREA_MIN_M2,
  EIGHT_CON,
  MAXSIZE
);

// 3) Classified HAND Image (<= 3 m) AND Urban
var img_ClassifiedSlicedHAND_3m_HotSpot = hotspotsByArea(
  classifiedImgHAND_LandCover_3m,   // binary selfMask image
  'Classified HAND (<=3 m) - Hotspots',
  AREA_MIN_M2,
  EIGHT_CON,
  MAXSIZE
);
// 4) Classified HAND Image (<= 4 m) AND Urban
var img_ClassifiedSlicedHAND_4m_HotSpot = hotspotsByArea(
  classifiedImgHAND_LandCover_4m,   // binary selfMask image
  'Classified HAND (<=4 m) - Hotspots',
  AREA_MIN_M2,
  EIGHT_CON,
  MAXSIZE
);
// 5) Classified HAND Image (<= 5 m) AND Urban
var img_ClassifiedSlicedHAND_5m_HotSpot = hotspotsByArea(
  classifiedImgHAND_LandCover_5m,   // binary selfMask image
  'Classified HAND (<=5 m) - Hotspots',
  AREA_MIN_M2,
  EIGHT_CON,
  MAXSIZE
);

Map.addLayer(setor_risco.filter(ee.Filter.eq('tipolo_g1', 'Inundação')),{},"CPRM Sectors")
//-------

//Export
var assetPathEnchente = '.../assets/ProjetoEnchente/';

Export.image.toAsset({
      image:img_ClassifiedRF_HotSpot.hotspots.select(['classification']),
      description:"img_ClassificadaRF_HotSpot",
      assetId:assetPathEnchente+"imgPosClassificadaSemiSuperv_riscoInundacao",
      region:region,
      scale:10,
      maxPixels:1e10,
})
Export.image.toDrive({
  image: img_ClassifiedRF_HotSpot.hotspots.select(['classification']),
  description: 'imgPosClassificadaSemiSuperv_riscoInundacao',
  folder:"projetoEnchenteAssets",
  region: region,
  scale: 10,
  maxPixels: 1e10
});

Export.image.toAsset({
      image:img_ClassifiedKMeans_HotSpot.hotspots.select(['cluster']),
      description:"img_ClassificadaKMeans_HotSpot",
      assetId:assetPathEnchente+"imgPosClassificadaNaoSuperv_riscoInundacao",
      region:region,
      scale:10,
      maxPixels:1e10,
})
Export.image.toDrive({
  image: img_ClassifiedKMeans_HotSpot.hotspots.select(['cluster']),
  description: 'imgPosClassificadaNaoSuperv_riscoInundacao',
  folder:"projetoEnchenteAssets",
  region: region,
  scale: 10,
  maxPixels: 1e10
});

Export.image.toAsset({
      image:img_ClassifiedSlicedHAND_3m_HotSpot.hotspots.select(['classification_hand']),
      description:"img_ClassificadaSlicedHAND_3m_HotSpot",
      assetId:assetPathEnchente+"imgPosClassificadaSlicedHAND_3m_riscoInundacao",
      region:region,
      scale:10,
      maxPixels:1e10,
})
Export.image.toDrive({
  image: img_ClassifiedSlicedHAND_3m_HotSpot.hotspots.select(['classification_hand']),
  description: 'img_ClassificadaSlicedHAND_3m_HotSpot',
  folder:"projetoEnchenteAssets",
  region: region,
  scale: 10,
  maxPixels: 1e10
});

Export.image.toAsset({
      image:img_ClassifiedSlicedHAND_4m_HotSpot.hotspots.select(['classification_hand']),
      description:"img_ClassificadaSlicedHAND_4m_HotSpot",
      assetId:assetPathEnchente+"imgPosClassificadaSlicedHAND_4m_riscoInundacao",
      region:region,
      scale:10,
      maxPixels:1e10,
})
Export.image.toDrive({
  image: img_ClassifiedSlicedHAND_4m_HotSpot.hotspots.select(['classification_hand']),
  description: 'img_ClassificadaSlicedHAND_4m_HotSpot',
  folder:"projetoEnchenteAssets",
  region: region,
  scale: 10,
  maxPixels: 1e10
});

Export.image.toAsset({
      image:img_ClassifiedSlicedHAND_5m_HotSpot.hotspots.select(['classification_hand']),
      description:"img_ClassificadaSlicedHAND_5m_HotSpot",
      assetId:assetPathEnchente+"imgPosClassificadaSlicedHAND_5m_riscoInundacao",
      region:region,
      scale:10,
      maxPixels:1e10,
})
Export.image.toDrive({
  image: img_ClassifiedSlicedHAND_5m_HotSpot.hotspots.select(['classification_hand']),
  description: 'img_ClassificadaSlicedHAND_5m_HotSpot',
  folder:"projetoEnchenteAssets",
  region: region,
  scale: 10,
  maxPixels: 1e10
});
