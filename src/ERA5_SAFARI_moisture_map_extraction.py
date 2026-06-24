# -*- coding: utf-8 -*-
"""
Download ERA5 moisture and column-water map data for the SAFARI region.

Saves one merged output file to ../data/processed/ and uses a run-specific
temporary directory for monthly CDS downloads.

View queue progress at: https://cds.climate.copernicus.eu/requests

@author: jtomfarrar
jfarrar@whoi.edu
"""
# %%
import os
from pathlib import Path

home_dir = Path.home()
os.chdir(home_dir / 'Python/ERA5_extraction/src')

# %%
import ERA5_extraction_tool

# %%
# N, W, S, E bounding box: lat0+dlat, lon0-dlon, lat0-dlat, lon0+dlon
REGION = dict(
    region_name='SAFARI_2025_2026',
    lon0=-161,
    lat0=35,
    dlon=40,
    dlat=20,
    start_year=2025,
    start_month=10,
    end_year=2025,
    end_month=12,
    out_path='../data/processed/',
)

# %%
out_path = Path(REGION['out_path'])
out_path.mkdir(parents=True, exist_ok=True)

date_label = ERA5_extraction_tool.date_range_label(
    REGION['start_year'],
    REGION['start_month'],
    REGION['end_year'],
    REGION['end_month'],
)
tmp_path = out_path / 'tmp' / f"{REGION['region_name']}_moisture_{date_label}"
tmp_path.mkdir(parents=True, exist_ok=True)

output_file = out_path / f"ERA5_surface_{REGION['region_name']}_moisture_{date_label}.nc"

print(f"Moisture data -> {output_file}")
print(f"Monthly temp  -> {tmp_path}")

# %%
# Download moisture data one month at a time to stay within CDS size limits
ERA5_extraction_tool.extract_monthly_range(
    REGION['lon0'],
    REGION['lat0'],
    REGION['dlon'],
    REGION['dlat'],
    REGION['start_year'],
    REGION['start_month'],
    REGION['end_year'],
    REGION['end_month'],
    'moisture',
    output_file,
    tmp_path,
    monthly_file_prefix=f"ERA5_surface_{REGION['region_name']}_moisture",
)

# %%
