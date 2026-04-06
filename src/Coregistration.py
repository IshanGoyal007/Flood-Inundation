#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Oct  8 15:37:59 2025

@author: ishan
"""

import os
import rasterio
from rasterio.warp import reproject, Resampling

def reproj_match(infile, match_ras, out_dir, file_name):
    """
    Coregisters (reprojects + resamples) `infile` tif to match the CRS,
    extent, resolution, and alignment of `match_ras`.
    """
    
    with rasterio.open(match_ras) as match:
        match_crs = match.crs
        match_transform = match.transform
        match_width = match.width
        match_height = match.height

        with rasterio.open(infile) as src:
            dst_kwargs = src.meta.copy()
            dst_kwargs.update({
                "crs": match_crs,
                "transform": match_transform,
                "width": match_width,
                "height": match_height,
                "nodata": 0
            })

            os.makedirs(out_dir, exist_ok=True)
            outfile = os.path.join(out_dir, f"{file_name}_coreg.tif")

            with rasterio.open(outfile, "w", **dst_kwargs) as dst:
                for i in range(1, src.count + 1):
                    reproject(
                        source=rasterio.band(src, i),
                        destination=rasterio.band(dst, i),
                        src_transform=src.transform,
                        src_crs=src.crs,
                        dst_transform=match_transform,
                        dst_crs=match_crs,
                        resampling=Resampling.bilinear
                    )

    print(f"✅ Coregistration complete: {outfile}")
    return outfile


def coregister_all(input_dir, reference_dem, output_dir):
    """
    Coregisters all tifs in `input_dir` to the same reference tif.
    Skips the reference file itself if it's in the same folder.
    """
    os.makedirs(output_dir, exist_ok=True)
    dem_files = [f for f in os.listdir(input_dir) if f.lower().endswith(".tif")]

    if not dem_files:
        print("⚠️ No .tif files found in input directory.")
        return

    ref_name = os.path.basename(reference_dem)
    print(f"Found {len(dem_files)} tif in {input_dir}.")
    print(f"Using '{ref_name}' as reference tif.\n")

    for dem in dem_files:
        if dem == ref_name:
            print(f"⏩ Skipping reference tif: {dem}")
            continue

        infile = os.path.join(input_dir, dem)
        name = os.path.splitext(dem)[0]
        try:
            reproj_match(infile, reference_dem, output_dir, name)
        except Exception as e:
            print(f"❌ Failed to coregister {tif}: {e}")

    print("\n🎯 All DEMs processed and saved to:", output_dir)


if __name__ == "__main__":
    # === USER INPUTS ===
    input_directory = "/home/ishan/Data/EYE/clipped"        # folder containing all DEMs
    reference_dem = "/home/ishan/Data/EYE/clipped_tif/output_hh_clipped.tif"  # one of them as reference
    output_directory = "/home/ishan/Data/EYE/clipped/Output"

    # === RUN COREISTRATION ===
    coregister_all(input_directory, reference_dem, output_directory)
