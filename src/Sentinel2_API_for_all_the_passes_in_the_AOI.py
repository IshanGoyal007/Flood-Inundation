#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Dec 13 21:33:39 2025

@author: ishan
"""

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Dec 13 21:08:43 2025

@author: ishan
"""

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Dec 13 20:57:10 2025

@author: ishan
"""

import os
from datetime import date
import requests
import pandas as pd
import geopandas as gpd
from shapely.geometry import shape
from shapely.ops import unary_union

# --------------------------------------------------
# USER CONFIGURATION
# --------------------------------------------------

copernicus_user = os.getenv("goyalishan007@gmail.com")       # Copernicus username
copernicus_password = os.getenv("Ishangoyal@2728")          # Copernicus password

aoi_file = "/home/ishan/Data/Ishan_Document/EYE/Uttarakhand/Uttarkashi_AOI.geojson"
data_collection = "SENTINEL-2"   # SENTINEL-2 for L2A

# DOWNLOAD DIRECTORY (ADDED)
download_dir = "/home/ishan/Data/Ishan_Document/EYE/Sentinel2"
os.makedirs(download_dir, exist_ok=True)

# Fixed date range
start_date = date(2025, 7, 20)
end_date   = date(2025, 8, 20)

start_date_string = start_date.strftime("%Y-%m-%d")
end_date_string   = end_date.strftime("%Y-%m-%d")   

# --------------------------------------------------
# AOI: GEOJSON → WKT
# --------------------------------------------------

gdf = gpd.read_file(aoi_file)
aoi_geom = unary_union(gdf.geometry)
aoi_wkt = aoi_geom.wkt

# --------------------------------------------------
# AUTHENTICATION
# --------------------------------------------------

def get_keycloak(username: str, password: str) -> str:
    data = {
        "client_id": "cdse-public",
        "username": "goyalishan007@gmail.com",
        "password": "Ishangoyal@2728",
        "grant_type": "password",
    }

    r = requests.post(
        "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token",
        data=data,
    )
    r.raise_for_status()
    return r.json()["access_token"]

# --------------------------------------------------
# SEARCH PRODUCTS
# --------------------------------------------------

query_url = (
    "https://catalogue.dataspace.copernicus.eu/odata/v1/Products?"
    f"$filter=Collection/Name eq '{data_collection}' "
    f"and OData.CSC.Intersects(area=geography'SRID=4326;{aoi_wkt}') "
    f"and ContentDate/Start ge {start_date_string}T00:00:00.000Z "
    f"and ContentDate/Start le {end_date_string}T23:59:59.999Z"
    "&$count=True&$top=1000"
)

response = requests.get(query_url)
response.raise_for_status()
json_ = response.json()

# --------------------------------------------------
# PROCESS RESULTS
# --------------------------------------------------

p = pd.DataFrame.from_dict(json_["value"])

if p.empty:
    print("❌ No data found for given date range and AOI")
    exit()

p["geometry"] = p["GeoFootprint"].apply(shape)
productDF = gpd.GeoDataFrame(p, geometry="geometry")

# Remove L1C, keep only L2A
productDF = productDF[~productDF["Name"].str.contains("L1C")]

print(f"✅ Total Sentinel-2 L2A tiles found: {len(productDF)}")

productDF["identifier"] = productDF["Name"].str.split(".").str[0]

# --------------------------------------------------
# DOWNLOAD PRODUCTS
# --------------------------------------------------

session = requests.Session()
token = get_keycloak(copernicus_user, copernicus_password)
session.headers.update({"Authorization": f"Bearer {token}"})

for idx, feat in enumerate(productDF.iterfeatures(), start=1):
    try:
        product_id = feat["properties"]["Id"]
        identifier = feat["properties"]["identifier"]
        name = feat["properties"]["Name"]

        print(f"[{idx}/{len(productDF)}] Downloading: {name}")

        url = (
            f"https://catalogue.dataspace.copernicus.eu/odata/v1/"
            f"Products({product_id})/$value"
        )

        response = session.get(url, allow_redirects=False)

        while response.status_code in (301, 302, 303, 307):
            url = response.headers["Location"]
            response = session.get(url, allow_redirects=False)

        file_response = session.get(url, stream=True)
        file_response.raise_for_status()

        output_path = os.path.join(download_dir, f"{identifier}.zip")

        with open(output_path, "wb") as f:
            for chunk in file_response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        print(f"✔ Downloaded: {output_path}")

    except Exception as e:
        print(f"⚠ Failed to download product {name}: {e}")

print("🎉 Download completed")
