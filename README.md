# Flood-Inundation


1) Overview
This project presents an Earth Observation (EO) and SAR-based flood inundation mapping and agricultural impact assessment for Karamchedu Mandal, which was severely affected by Cyclone Montha on 28 October 2025.
The analysis integrates:

Sentinel-1 SAR data — for cloud-independent flood detection via backscatter change analysis
Sentinel-2 optical data — for vegetation (NDVI) and water index (NDWI) computation

The study demonstrates the power of multi-sensor remote sensing for rapid disaster response and agricultural damage quantification.

🗺️ Study Area
Karamchedu Mandal is located in Bapatla District, Andhra Pradesh — a low-lying, intensively cultivated coastal region dominated by paddy fields and irrigated croplands. Its proximity to coastal systems and flat terrain makes it highly vulnerable to cyclonic rainfall and flood inundation during the northeast monsoon.

2) Objectives

Map flood inundation extent using SAR backscatter difference analysis
Identify excess surface water accumulation using NDWI
Quantify agricultural damage using NDVI change analysis


3) Datasets Used
SensorProductResolutionPolarizationSourceSentinel-1GRD (IW Mode)10 mVV & VHASF Search APISentinel-2L2A (MSI)10 m—Copernicus Open Access Hub
SAR Acquisition Dates:

Pre-event: 26 October 2025 (before Cyclone Montha)
Post-event: 01 November 2025 (after Cyclone Montha)


4) Methodology
Sentinel-1 (VV & VH)              Sentinel-2
        │                               │
   Calibration                    Band Extraction
        │                          (B03, B04, B08)
   Speckle Filtering                    │
        │                    ┌──────────┴──────────┐
   Terrain Correction        │                     │
        │                   NDVI                  NDWI
   Linear to dB             (NIR-Red)/(NIR+Red)   (Green-NIR)/(Green+NIR)
        │                         │                     │
   Export to TIFF                 └──────────┬──────────┘
        │                                    │
   Backscatter Difference          Clipping to AOI
        │                                    │
        └──────────────┬─────────────────────┘
                       │
            Interpretation & Impact Assessment
   
4.1 SAR Preprocessing (SNAP)
Sentinel-1 GRD data was processed through the standard SNAP workflow:

Radiometric Calibration — corrects uneven signal response across the image
Speckle Filtering — removes grainy noise inherent to SAR imagery
Terrain Correction — flattens topographic distortion using a DEM
Linear to dB Conversion — transforms backscatter values to decibel scale

4.2 Flood Inundation Mapping
Flooded surfaces act as specular reflectors, producing low backscatter in SAR imagery. Inundation was detected by computing the backscatter difference between pre- and post-event images for both VV and VH polarizations.
4.3 NDWI — Excess Surface Water
NDWI=NIR−SWIRNIR+SWIRNDWI = \frac{NIR - SWIR}{NIR + SWIR}NDWI=NIR+SWIRNIR−SWIR​
High NDWI values indicate open water and saturated soil — used to validate and complement SAR-based flood mapping.
4.4 NDVI — Agricultural Impact
NDVI=NIR−RedNIR+RedNDVI = \frac{NIR - Red}{NIR + Red}NDVI=NIR+RedNIR−Red​
A decline in post-event NDVI signals crop submergence, waterlogging stress, and physical damage to standing crops.

🗂️ Repository Structure
├── Sentinel2_API_for_all_the_passes_in_the_AOI.py   # Sentinel-2 data download via Copernicus API
├── GEE_Python_code_Sentinel1.py                      # Sentinel-1 time-series export via Google Earth Engine
├── NDVI_NDWI_Indices_generation_and_clipping_wrt_AOI.py  # NDVI & NDWI computation and AOI clipping
├── Coregistration.py                                 # Spatial coregistration of raster datasets
└── README.md

5 Scripts Description
5.1 Sentinel2_API_for_all_the_passes_in_the_AOI.py
Downloads all available Sentinel-2 L2A tiles intersecting a given AOI from the Copernicus Data Space Ecosystem API.
Key features:

Reads AOI from a GeoJSON file and converts to WKT for spatial filtering
Authenticates via Keycloak token (Copernicus credentials)
Queries the OData catalogue for a user-defined date range
Filters to L2A products only (excludes L1C)
Downloads all matching products as .zip archives with redirect handling

Dependencies: requests, pandas, geopandas, shapely

5.2 GEE_Python_code_Sentinel1.py
Exports a Sentinel-1 SAR time series (descending orbit, IW mode) to Google Drive using the Google Earth Engine Python API.
Key features:

Filters by AOI, date range, orbit direction, and polarization (VV + VH)
Converts backscatter from linear to dB scale
Stacks all acquisitions into a single multi-band image with date-labeled bands
Exports to Google Drive at 10 m resolution with task status monitoring

**Dependencies**: earthengine-api, geemap

5.3 NDVI_NDWI_Indices_generation_and_clipping_wrt_AOI.py
Computes NDVI and NDWI from Sentinel-2 .jp2 band files and clips the output to an AOI GeoJSON.
Key features:

Groups .jp2 raster files by tile and date automatically
Computes NDVI (B08, B04) and NDWI (B03, B08) for each acquisition
Reprojects the AOI GeoJSON to match raster CRS if needed
Saves clipped GeoTIFF outputs per date and index

Dependencies: numpy, rasterio, fiona, shapely, pyproj

5.4 Coregistration.py
Spatially coregisters (reprojects + resamples) a set of raster files to match a reference raster's CRS, extent, and resolution.
Key features:

Matches CRS, pixel alignment, and spatial extent to a reference .tif
Uses bilinear resampling for smooth interpolation
Batch-processes all .tif files in a directory
Skips the reference file automatically

Dependencies: rasterio

6 Results Summary
Flood Inundation (SAR)
SAR backscatter difference maps revealed extensive inundation across low-lying agricultural fields in Karamchedu Mandal. The VH polarization was particularly effective in detecting inundated crop areas, and results remained valid despite heavy cloud cover obscuring optical data.
Excess Water (NDWI)
Post-cyclone NDWI maps showed widespread surface water accumulation in agricultural plots and drainage channels. High NDWI values spatially coincided with SAR-detected flood zones, validating the inundation mapping.
Agricultural Damage (NDVI)
NDVI analysis revealed a significant reduction in vegetation vigor across large portions of the mandal between pre- and post-event imagery. The spatial overlap between NDVI decline and flood extent confirmed extensive crop stress and potential yield loss from prolonged waterlogging.

7 Installation & Setup
Prerequisites
bashpip install numpy rasterio fiona shapely pyproj geopandas requests pandas earthengine-api geemap
Google Earth Engine Authentication
bashearthengine authenticate
Copernicus API Credentials
Set your credentials as environment variables before running the Sentinel-2 download script:
bashexport COPERNICUS_USER="your_email@example.com"
export COPERNICUS_PASSWORD="your_password"

⚠️ Never hardcode credentials in scripts. Use environment variables or a .env file.


8 Usage
Step 1 — Download Sentinel-2 Data
bashpython Sentinel2_API_for_all_the_passes_in_the_AOI.py
Update aoi_file, download_dir, and date range in the script before running.
Step 2 — Export Sentinel-1 Time Series (GEE)
bashpython GEE_Python_code_Sentinel1.py
Update geojson_path, start_date, end_date, and your GEE PROJECT_ID.
Step 3 — Compute NDVI & NDWI
bashpython NDVI_NDWI_Indices_generation_and_clipping_wrt_AOI.py
Update raster_folder, geojson_path, and output_folder.
Step 4 — Coregister Rasters
bashpython Coregistration.py
Update input_directory, reference_dem, and output_directory.

9 Key References

ESA Sentinel-1 Technical Guide — sentinel.esa.int
ESA Sentinel-2 Technical Guide — sentinel.esa.int
Copernicus Data Space Ecosystem — dataspace.copernicus.eu
Google Earth Engine Python API — developers.google.com/earth-engine
SNAP (Sentinel Application Platform) — step.esa.int

10 Author
Ishan Goyal
Image Analyst — Remote Sensing & GIS
