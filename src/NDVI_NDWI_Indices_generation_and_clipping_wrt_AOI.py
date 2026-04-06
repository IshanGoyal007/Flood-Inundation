#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Dec 17 10:14:19 2025

@author: ishan
"""

import os
import glob
import numpy as np
import rasterio
from rasterio.mask import mask
import fiona
from shapely.geometry import shape, mapping
from shapely.ops import transform
from pyproj import Transformer
from collections import defaultdict

# =========================
# USER INPUTS
# =========================
raster_folder = "/path/to/input_rasters"
geojson_path = "/path/to/clip_area.geojson"
output_folder = "/path/to/output_indices"

os.makedirs(output_folder, exist_ok=True)

# =========================
# READ GEOJSON
# =========================
with fiona.open(geojson_path, "r") as g:
    geo_crs = g.crs
    geo_shapes = [shape(feat["geometry"]) for feat in g]

# =========================
# GROUP RASTERS BY DATE/TILE
# =========================
band_files = glob.glob(os.path.join(raster_folder, "*.jp2"))

groups = defaultdict(dict)

for f in band_files:
    name = os.path.basename(f)
    parts = name.split("_")

    tile_date = "_".join(parts[:2])      # T44PMC_20251107T050231
    band = parts[2]                      # B02, B03, B04, B08

    groups[tile_date][band] = f

# =========================
# PROCESS EACH DATE
# =========================
for key, bands in groups.items():

    if not {"B03", "B04", "B08"}.issubset(bands):
        print(f"⚠️ Skipping {key} (missing bands)")
        continue

    print(f"\nProcessing {key}")

    with rasterio.open(bands["B08"]) as nir_src, \
         rasterio.open(bands["B04"]) as red_src, \
         rasterio.open(bands["B03"]) as green_src:

        nir = nir_src.read(1).astype("float32")
        red = red_src.read(1).astype("float32")
        green = green_src.read(1).astype("float32")

        # Avoid divide by zero
        np.seterr(divide="ignore", invalid="ignore")

        ndvi = (nir - red) / (nir + red)
        ndwi = (green - nir) / (green + nir)

        meta = nir_src.meta.copy()
        meta.update(dtype="float32", count=1, nodata=np.nan)

        raster_crs = nir_src.crs

        # =========================
        # REPROJECT GEOJSON IF NEEDED
        # =========================
        if geo_crs != raster_crs:
            transformer = Transformer.from_crs(
                geo_crs, raster_crs, always_xy=True
            )
            project = lambda x, y: transformer.transform(x, y)
            shapes_proj = [mapping(transform(project, g)) for g in geo_shapes]
        else:
            shapes_proj = [mapping(g) for g in geo_shapes]

        # =========================
        # SAVE TEMP NDVI / NDWI
        # =========================
        temp_ndvi = os.path.join(output_folder, f"{key}_NDVI_temp.tif")
        temp_ndwi = os.path.join(output_folder, f"{key}_NDWI_temp.tif")

        with rasterio.open(temp_ndvi, "w", **meta) as dst:
            dst.write(ndvi, 1)

        with rasterio.open(temp_ndwi, "w", **meta) as dst:
            dst.write(ndwi, 1)

    # =========================
    # CLIP NDVI & NDWI
    # =========================
    for idx, temp_file in [("NDVI", temp_ndvi), ("NDWI", temp_ndwi)]:
        out_file = os.path.join(output_folder, f"{key}_{idx}_clipped.tif")

        with rasterio.open(temp_file) as src:
            try:
                clipped, transform_out = mask(
                    src, shapes_proj, crop=True, nodata=np.nan
                )
            except ValueError:
                print(f"⚠️ No overlap for {idx}")
                continue

            out_meta = src.meta.copy()
            out_meta.update({
                "height": clipped.shape[1],
                "width": clipped.shape[2],
                "transform": transform_out
            })

            with rasterio.open(out_file, "w", **out_meta) as dst:
                dst.write(clipped)

        os.remove(temp_file)

        print(f"✅ Saved {idx}: {out_file}")

print("\n🎉 NDVI & NDWI calculation and clipping completed!")
