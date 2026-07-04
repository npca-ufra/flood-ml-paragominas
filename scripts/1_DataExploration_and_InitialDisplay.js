// =====================================================
// DIGITAL ELEVATION MODEL (DEM)
// Source: ANADEM - Digital Terrain Model
// https://www.ufrgs.br/hge/anadem-modelo-digital-de-terreno-mdt/
// =====================================================
var anadem = ee.Image('projects/et-brasil/assets/anadem/v1');

// Remove NoData values (-9999) and clip to the study area
var elevation = anadem
  .updateMask(anadem.neq(-9999))
  .clip(geometry);

// Elevation visualization parameters (meters)
var elevationVis = {
  min: 70,
  max: 152.0,
  palette: ['006600', '002200', 'fff700', 'ab7634', 'c4d0ff', 'ffffff']
};

// Rename the band and reproject to WGS84 at 10 m resolution
elevation = elevation.rename("elevacao").reproject({
  crs: 'EPSG:4326',
  scale: 10
});

// Add the DEM to the map
Map.addLayer(elevation, elevationVis, 'Elevation (m)');


// =====================================================
// SOIL HYDRAULIC CONDUCTIVITY (Ks)
// Source: HiHydroSoil v2.0
// https://gee-community-catalog.org/projects/hihydro_soil/#citation-related-publications
// =====================================================
var HiHydro = ee.ImageCollection(
  'projects/sat-io/open-datasets/HiHydroSoilv2_0/ksat'
);

// Color palette for visualization
var palettes = require('users/gena/packages:palettes');
var ksatVis = {
  min: 3,
  max: 16,
  palette: palettes.cmocean.Delta[7]
};

// Select the first image, adjust the scale (cm/day) and clip the study area
var ksat = HiHydro.first()
  .multiply(0.0001)
  .clip(geometry);

// Fill pixels without data with a sentinel value (1000)
var mask = ksat.unmask(1000).clip(geometry);

// Identify the artificially filled pixels
var targetMask = mask.eq(1000);

// Compute the median of neighboring pixels (45x45 pixel window)
var medianNeighbors = mask.focal_median({
  radius: 45,
  kernelType: 'square',
  units: 'pixels'
});

// Replace pixels without data with the neighbors' median
var replaced = mask.where(targetMask, medianNeighbors);

// Rename the band and reproject to WGS84 at 30 m resolution
var ksatFilledData = replaced
  .rename("condutivid_hidraulica_solo")
  .reproject({
    crs: 'EPSG:4326',
    scale: 30
  });

// Add the soil hydraulic conductivity to the map
Map.addLayer(
  ksatFilledData,
  ksatVis,
  'Soil hydraulic conductivity (cm/d)'
);


// =====================================================
// LAND USE AND LAND COVER
// Source: MapBiomas - Sentinel-2 Collection (10 m)
// https://brasil.mapbiomas.org/codigos-e-ferramentas/
// =====================================================
var finalYear = 2022;
var initialYear = 2016;

// Official MapBiomas palette (classification level 9)
var palettesMapBiomas = require('users/mapbiomas/modules:Palettes.js');
palettesMapBiomas = palettesMapBiomas.get('classification9');

var mapbiomasVis = {
  min: 0,
  max: 69,
  palette: palettesMapBiomas,
  format: 'png'
};

// Load the MapBiomas collection and select the final year
var MapBiomas_collection = ee.Image(
  'projects/mapbiomas-public/assets/brazil/lulc/collection_S2_beta/collection_LULC_S2_beta'
).clip(geometry);

var MapBiomas = MapBiomas_collection
  .select('classification_' + finalYear);

// Add the land use and land cover map
Map.addLayer(
  MapBiomas,
  mapbiomasVis,
  'Land use and land cover (10 m) - ' + finalYear,
  true
);

// Rename the band
MapBiomas = MapBiomas.rename("usocobersolo_classification_2022");

/*
MapBiomas classes considered:
3  - Forest Formation                  | #1f8d49
9  - Forest Plantation                 | #7a5900
11 - Wetland / Marsh Area              | #519799
12 - Grassland Formation               | #d6bc74
15 - Pasture                           | #edde8e
19 - Temporary Crop                    | #C27BA0
24 - Urban Area                        | #d4271e
25 - Other Non-Vegetated Areas         | #db4d4f
33 - River, Lake and Ocean             | #2532e4
*/


// =====================================================
// FLOOD RISK AREAS
// Source: Geological Survey of Brazil (CPRM)
// https://geoportal.sgb.gov.br/desastres/
// =====================================================

// Filter only sectors classified as flooding
riskSector = riskSector.filter(
  ee.Filter.eq('tipolo_g1', 'Inundação')
);

// Convert the risk sectors into geometry
var riskSectorGeometry = riskSector.geometry();

// Add the flood risk areas to the map
Map.addLayer(
  riskSectorGeometry,
  {},
  "Risk sectors - Flooding (CPRM)"
);


// =====================================================
// HYDROGRAPHY
// Source: IBGE / Instituto Cerrado
// =====================================================

// Add river vectors
Map.addLayer(
  rivers,
  { color: 'black' },
  "Rivers"
);
