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


def date_range_label(region):
    return (
        f"{region['start_year']:04d}{region['start_month']:02d}_"
        f"{region['end_year']:04d}{region['end_month']:02d}"
    )


def tmp_dir_path(out_path, region):
    return out_path / 'tmp' / f"{region['region_name']}_{date_range_label(region)}"


def monthly_file_path(tmp_path, region, year, month, kind):
    if kind == 'met':
        filename = f"ERA5_surface_{region['region_name']}_{year:04d}_{month:02d}.nc"
    elif kind == 'waves':
        filename = f"ERA5_surface_{region['region_name']}_waves_{year:04d}_{month:02d}.nc"
    else:
        raise ValueError(f"Unknown file kind: {kind}")
    return tmp_path / filename


def output_file_path(out_path, region, kind):
    label = date_range_label(region)
    if kind == 'met':
        filename = f"ERA5_surface_{region['region_name']}_{label}.nc"
    elif kind == 'waves':
        filename = f"ERA5_surface_{region['region_name']}_waves_{label}.nc"
    else:
        raise ValueError(f"Unknown file kind: {kind}")
    return out_path / filename


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


def download_monthly_files(region, tmp_path, kind):
    monthly_files = []
    year_months = list(iter_year_months(
        region['start_year'],
        region['start_month'],
        region['end_year'],
        region['end_month'],
    ))

    print(f"\nDownloading {kind}: {region['region_name']}, {date_range_label(region)}")
    print('View queue: https://cds.climate.copernicus.eu/requests')

    for year, month in year_months:
        monthly_file = monthly_file_path(tmp_path, region, year, month, kind)
        if monthly_file.exists():
            print(f"  {year:04d}-{month:02d}: already exists, skipping")
        else:
            print(f"  {year:04d}-{month:02d}: downloading ...")
            ERA5_extraction_tool.tic()
            if kind == 'met':
                ERA5_extraction_tool.get_surface_vars(
                    region['lon0'], region['lat0'], region['dlon'], region['dlat'],
                    str(year), [f"{month:02d}"], str(monthly_file),
                )
            elif kind == 'waves':
                ERA5_extraction_tool.get_wave_vars(
                    region['lon0'], region['lat0'], region['dlon'], region['dlat'],
                    str(year), [f"{month:02d}"], str(monthly_file),
                )
            else:
                raise ValueError(f"Unknown file kind: {kind}")
            ERA5_extraction_tool.toc()
            time_module.sleep(5)
        monthly_files.append(monthly_file)

    return monthly_files


tmp_path = tmp_dir_path(out_path, REGION)
tmp_path.mkdir(parents=True, exist_ok=True)

output_file_met = output_file_path(out_path, REGION, 'met')
output_file_waves = output_file_path(out_path, REGION, 'waves')

print(f"Surface met  -> {output_file_met}")
print(f"Wave data    -> {output_file_waves}")
print(f"Monthly temp -> {tmp_path}")

# %%
# Download surface met one month at a time to stay within CDS size limits
monthly_met_files = download_monthly_files(REGION, tmp_path, 'met')

# %%
# Merge monthly surface met files → final combined file
merge_monthly_files(monthly_met_files, output_file_met)

# %%
# Download wave data one month at a time
monthly_wave_files = download_monthly_files(REGION, tmp_path, 'waves')

# %%
# Merge monthly wave files → final combined file
merge_monthly_files(monthly_wave_files, output_file_waves)
shutil.rmtree(tmp_path)

# %%
