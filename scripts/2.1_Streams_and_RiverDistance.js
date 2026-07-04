// =============================================================================
// Euclidean distance to rivers/streams in Paragominas
// Author: GILBERTO N S JR
// Description: creates a buffer around the drainage network, rasterizes it as a
//              "target" and computes the per-pixel Euclidean distance to those targets.
// External dependencies (Assets):
//  - /TrechosDrenagemParagominas_Intersesct
// Preconditions (defined outside this snippet):
//  - roi: ee.Geometry/ee.FeatureCollection of the region of interest. A rectangle over the urban area.
//  - corrego_rio_urain_pgm: ee.FeatureCollection with additional streams.
// Note: base projection taken from Dynamic World V1 (2024).
// =============================================================================

// ---- General parameters -----------------------------------------------------
var pixelSize = 10; // [m] target resolution for reprojection and export

// ---- Drainage network (rivers/streams) --------------------------------------
// Region of interest: Paragominas drainage reaches near the urban area.
var drainagesPgm = ee.FeatureCollection(
  '.../assets/TrechosDrenagemParagominas_Intersesct'
);
Map.addLayer(drainagesPgm, {}, 'Drainages (rivers)', false)

var drainagesWithStreams = roi.intersection(drainagesPgm, 0.5)
drainagesWithStreams = drainagesWithStreams.union(corrego_rio_urain_pgm)
Map.addLayer(drainagesWithStreams, {}, 'Drainages (rivers + streams)', false)

// ---- Buffer around the water courses ----------------------------------------
var drainagesBuffer  = drainagesWithStreams.buffer(pixelSize,0.5)
Map.addLayer(drainagesBuffer, {}, 'Drainages (buffer)', false)

// ---- Base projection from Dynamic World (2024) ------------------------------
// Imports Dynamic World, aggregates the 2024 median and takes the projection for standardization.
var imgDw2024  = ee.ImageCollection("GOOGLE/DYNAMICWORLD/V1").filterBounds(roi).filterDate("2024-01-01","2025-01-01").median().select('label').clip(roi)
var baseProj  = imgDw2024 .projection()

// ---- Auxiliary image: zero background + "target" painted with 1 -------------
// distance() requires a "target" raster (1) within zeros to compute the distance to the target pixels.
var imgZeroBackground  = imgDw2024.multiply(0).reproject(baseProj,null, pixelSize)
var imgRiverTarget  = imgZeroBackground.paint(drainagesBuffer,1)

// ---- Euclidean Distance to rivers/streams (in meters) -----------------------
//Applies a kernel to identify each pixel's distance to the PGM rivers
var maxDistanceM = 2500// adjust according to the desired reach//4096//2048//512//50000;
var euclideanKernel = ee.Kernel.euclidean(maxDistanceM, 'meters')
var euclideanDist  = imgRiverTarget.distance(euclideanKernel).rename("DistanciaRio_m")

//Distance visualization
var distVis  = {min: 0, max: maxDistanceM}
Map.addLayer(euclideanDist.clip(roi), distVis, 'Euclidean distance to rivers');

// ---- Base path for export ---------------------------------------------------
var assetPath  = '.../assets/ProjetoEnchente/';

// ---- Export: vectors (unified rivers + streams) -----------------------------
//Export of the PGM river vectors with the addition of identified streams
Export.table.toAsset({
  collection:ee.FeatureCollection([ee.Feature(drainagesWithStreams)]),
  description: 'rios_corregos_pgm',
  assetId: assetPath+'rios_corregos_pgm'
})

Export.table.toDrive({
  collection:ee.FeatureCollection([ee.Feature(drainagesWithStreams)]),
  description: 'rios_corregos_pgm',
  folder:"projetoEnchenteAssets"
})

// ---- Export: distance raster in meters --------------------------------------
Export.image.toAsset({
  image: euclideanDist,
  assetId:assetPath+'distancia_rios',
  description: 'distancia_rios',
  scale: pixelSize,
  region: roi,
  crs: 'EPSG:4326',
  maxPixels: 1e10
});
