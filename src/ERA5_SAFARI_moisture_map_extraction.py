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
import shutil
from pathlib import Path

home_dir = Path.home()
os.chdir(home_dir / 'Python/ERA5_extraction/src')

# %%
import ERA5_extraction_tool
import time as time_module

# %%
import xarray as xr
import numpy as np

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


def iter_year_months(start_year, start_month, end_year, end_month):
    """Return inclusive (year, month) pairs for a month-based date range."""
    for month in [start_month, end_month]:
        if month < 1 or month > 12:
            raise ValueError("Months must be between 1 and 12.")

    start_index = start_year * 12 + start_month
    end_index = end_year * 12 + end_month
    if start_index > end_index:
        raise ValueError("Start month must be before or equal to end month.")

    for month_index in range(start_index, end_index + 1):
        year, zero_based_month = divmod(month_index - 1, 12)
        yield year, zero_based_month + 1


def merge_monthly_files(monthly_files, output_file):
    print(f"Merging {len(monthly_files)} monthly files -> {output_file}")
    ds = xr.open_mfdataset([str(f) for f in monthly_files], combine='by_coords', engine='h5netcdf')

    for var in list(ds.data_vars) + list(ds.coords):
        ds[var].encoding.clear()

    encoding = {}
    for var in list(ds.data_vars) + list(ds.coords):
        enc = {'zlib': True, 'complevel': 4}
        if np.issubdtype(ds[var].dtype, np.floating):
            enc['dtype'] = 'float32'
            enc['_FillValue'] = np.nan
        encoding[var] = enc

    ds.to_netcdf(output_file, encoding=encoding, engine='h5netcdf')
    ds.close()
    print('Done.')


date_label = (
    f"{REGION['start_year']:04d}{REGION['start_month']:02d}_"
    f"{REGION['end_year']:04d}{REGION['end_month']:02d}"
)
tmp_path = out_path / 'tmp' / f"{REGION['region_name']}_moisture_{date_label}"
tmp_path.mkdir(parents=True, exist_ok=True)

output_file = out_path / f"ERA5_surface_{REGION['region_name']}_moisture_{date_label}.nc"

print(f"Moisture data -> {output_file}")
print(f"Monthly temp  -> {tmp_path}")

# %%
# Download moisture data one month at a time to stay within CDS size limits
monthly_moisture_files = []
year_months = list(iter_year_months(
    REGION['start_year'],
    REGION['start_month'],
    REGION['end_year'],
    REGION['end_month'],
))

print(f"\nDownloading moisture: {REGION['region_name']}, {date_label}")
print('View queue: https://cds.climate.copernicus.eu/requests')

for year, month in year_months:
    monthly_file = tmp_path / f"ERA5_surface_{REGION['region_name']}_moisture_{year:04d}_{month:02d}.nc"
    if monthly_file.exists():
        print(f"  {year:04d}-{month:02d}: already exists, skipping")
    else:
        print(f"  {year:04d}-{month:02d}: downloading ...")
        ERA5_extraction_tool.tic()
        ERA5_extraction_tool.get_moisture_vars(
            REGION['lon0'], REGION['lat0'], REGION['dlon'], REGION['dlat'],
            str(year), [f"{month:02d}"], str(monthly_file),
        )
        ERA5_extraction_tool.toc()
        time_module.sleep(5)
    monthly_moisture_files.append(monthly_file)

# %%
# Merge monthly moisture files into final combined file
merge_monthly_files(monthly_moisture_files, output_file)
shutil.rmtree(tmp_path)

# %%
