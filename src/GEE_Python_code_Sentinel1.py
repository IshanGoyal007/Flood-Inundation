import ee
import geemap
import json
import time

# ---------------------------
# 1. AUTHENTICATION
# ---------------------------
PROJECT_ID = "utility-span-457806-m7"

try:
    ee.Initialize(project=PROJECT_ID)
except:
    ee.Authenticate()
    ee.Initialize(project=PROJECT_ID)

# ---------------------------
# 2. LOAD AOI (FIXED)
# ---------------------------
geojson_path = "/home/ishan/Data/Uttarkashi_AOI.geojson"

with open(geojson_path) as f:
    geojson_dict = json.load(f)

aoi_fc = geemap.geojson_to_ee(geojson_dict)
aoi = aoi_fc.geometry()   # ✅ IMPORTANT FIX

# ---------------------------
# 3. DATE RANGE
# ---------------------------
start_date = '2025-12-01'
end_date = '2025-12-31'

# ---------------------------
# 4. SENTINEL-1 (DESCENDING)
# ---------------------------
collection = (ee.ImageCollection('COPERNICUS/S1_GRD')
              .filterBounds(aoi)
              .filterDate(start_date, end_date)
              .filter(ee.Filter.eq('instrumentMode', 'IW'))
              .filter(ee.Filter.eq('orbitProperties_pass', 'DESCENDING'))
              .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VV'))
              .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VH'))
              .filter(ee.Filter.eq('resolution_meters', 10))
)

print("📊 Number of images:", collection.size().getInfo())

# ---------------------------
# 5. dB CONVERSION
# ---------------------------
def to_db(image):
    return ee.Image(10).multiply(image.log10()) \
        .copyProperties(image, ['system:time_start'])

collection = collection.map(to_db)

# ---------------------------
# 6. RENAME BANDS
# ---------------------------
def rename_bands(image):
    date = ee.Date(image.get('system:time_start')).format('dd_MM_YYYY')
    
    vv_name = ee.String('VV_').cat(date)
    vh_name = ee.String('VH_').cat(date)
    
    return image.select(['VV', 'VH']) \
                .rename([vv_name, vh_name])

renamed = collection.map(rename_bands)

# ---------------------------
# 7. STACK
# ---------------------------
stacked = renamed.toBands().clip(aoi)

# ---------------------------
# 8. CLEAN BAND NAMES
# ---------------------------
band_names = stacked.bandNames()

def clean_name(name):
    name = ee.String(name)
    parts = name.split('_')
    return ee.String(parts.slice(1).join('_'))

cleaned_names = band_names.map(clean_name)
stacked = stacked.rename(cleaned_names)

print("📊 Number of bands:", stacked.bandNames().size().getInfo())

# ---------------------------
# 9. EXPORT
# ---------------------------
task = ee.batch.Export.image.toDrive(
    image=stacked,
    description='S1_DESC_TimeSeries',
    folder='GEE_Exports',
    fileNamePrefix='S1_DESC',
    region=aoi,   # ✅ now correct
    scale=10,
    maxPixels=1e13
)

task.start()

print("🚀 Export started!")

# ---------------------------
# 10. MONITOR STATUS
# ---------------------------
while task.active():
    print("⏳ Exporting... please wait")
    time.sleep(30)

status = task.status()
print("🎯 Final Status:", status)

if status['state'] == 'COMPLETED':
    print("✅ Export completed! Check Google Drive.")
elif status['state'] == 'FAILED':
    print("❌ Export failed!")
    print("Error message:", status.get('error_message'))