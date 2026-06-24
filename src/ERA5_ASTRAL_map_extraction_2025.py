# -*- coding: utf-8 -*-
"""
Download ERA5 surface met and wave map data for the ASTRAL 2025 Bay of Bengal campaign.

Saves output to ../data/processed/ for use by ERA5_ASTRAL_plots_v2.py.

Run one cell at a time in VSCode IPython (large CDS downloads can take a while).
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
# Region configs -- select active region by setting REGION below
# N, W, S, E bounding box:  lat0+dlat, lon0-dlon, lat0-dlat, lon0+dlon
REGIONS = {
    'ASTRAL_big_2025': dict(
        region_name = 'ASTRAL_big_2025',
        lon0 = 85,     # center longitude; lon0 ± dlon = 70–100°E
        lat0 = 11,     # center latitude;  lat0 ± dlat =  1–21°N
        dlon = 15,
        dlat = 10,
        start_year = 2025,
        start_month = 4,
        end_year = 2025,
        end_month = 7,
        out_path = '../data/processed/',
    ),
    'SAFARI': dict(
        region_name = 'SAFARI',
        lon0 = -161,   # center longitude; lon0 ± dlon = 159–121°W
        lat0 = 35,     # center latitude;  lat0 ± dlat =  15–55°N
        dlon = 40,
        dlat = 20,
        start_year = 2024,
        start_month = 1,
        end_year = 2024,
        end_month = 12,
        out_path = '../data/processed/',
    ),
    'SAFARI_2025_2026': dict(
        region_name = 'SAFARI_2025_2026',
        lon0 = -161,   # center longitude; lon0 ± dlon = 159–121°W
        lat0 = 35,     # center latitude;  lat0 ± dlat =  15–55°N
        dlon = 40,
        dlat = 20,
        start_year = 2025,
        start_month = 10,
        end_year = 2026,
        end_month = 6,
        out_path = '../data/processed/',
    ),
}

REGION = REGIONS['SAFARI_2025_2026'] # REGIONS['ASTRAL_big_2025']  # <-- select active region here

# %%
out_path = Path(REGION['out_path'])
out_path.mkdir(parents=True, exist_ok=True)

date_label = ERA5_extraction_tool.date_range_label(
    REGION['start_year'],
    REGION['start_month'],
    REGION['end_year'],
    REGION['end_month'],
)
tmp_path = out_path / 'tmp' / f"{REGION['region_name']}_{date_label}"
tmp_path.mkdir(parents=True, exist_ok=True)

output_file_met = out_path / f"ERA5_surface_{REGION['region_name']}_{date_label}.nc"
output_file_waves = out_path / f"ERA5_surface_{REGION['region_name']}_waves_{date_label}.nc"

print(f"Surface met  -> {output_file_met}")
print(f"Wave data    -> {output_file_waves}")
print(f"Monthly temp -> {tmp_path}")

# %%
# Download surface met one month at a time to stay within CDS size limits
ERA5_extraction_tool.extract_monthly_range(
    REGION['lon0'],
    REGION['lat0'],
    REGION['dlon'],
    REGION['dlat'],
    REGION['start_year'],
    REGION['start_month'],
    REGION['end_year'],
    REGION['end_month'],
    'surface',
    output_file_met,
    tmp_path,
    monthly_file_prefix=f"ERA5_surface_{REGION['region_name']}",
    cleanup_tmp=False,
)

# %%
# Download wave data one month at a time
ERA5_extraction_tool.extract_monthly_range(
    REGION['lon0'],
    REGION['lat0'],
    REGION['dlon'],
    REGION['dlat'],
    REGION['start_year'],
    REGION['start_month'],
    REGION['end_year'],
    REGION['end_month'],
    'waves',
    output_file_waves,
    tmp_path,
    monthly_file_prefix=f"ERA5_surface_{REGION['region_name']}_waves",
    cleanup_tmp=True,
)

# %%
