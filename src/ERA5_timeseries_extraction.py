# -*- coding: utf-8 -*-
"""
Created on Wed Jan 20 11:02:33 2021

@author: jtomf
"""
# %%
# change to the directory where this script is located
import os

home_dir = os.path.expanduser("~")
os.chdir(home_dir+'/Python/ERA5_extraction/src')

# %%

import datetime as dt
from pathlib import Path
import ERA5_extraction_tool
from ERA5_timeseries_sites_config import SITES
import numpy as np
import time
import xarray as xr


# %%
site_name = 'Calabar_offshore' # 'Univ_of_Calabar' # 'ASTRAL_2025_WHOI43' # 'RAMA_12N' # 'SAFARI' # 'MVCO' # 'RAMA_12N', 'ASTRAL_2025_Ida', 'ASTRAL_2025_Kelvin', 'ASTRAL_2025_Planck', 'ASTRAL_2025_WHOI43', 'Endurance_RCA', 'SAFARI', 'MVCO'
print(f'Site: {site_name}  (options: {list(SITES.keys())})')

# %%

cfg       = SITES[site_name]
lon_pt    = cfg['lon_pt']
lat_pt    = cfg['lat_pt']
startdate = cfg['startdate']
enddate   = cfg['enddate']

out_path = '../data/processed/timeseries/' # this is where the extracted data will be saved
# create the output directory if it doesn't exist
if not os.path.exists(out_path):
    os.makedirs(out_path)


# %%
def open_timeseries_file(timeseries_file):
    # CDS may return a ZIP that contains separate surface and wave NetCDF files.
    # Convert that ZIP payload to a readable merged NetCDF file if needed.
    normalized_file = ERA5_extraction_tool._ensure_netcdf_from_cds(str(timeseries_file))
    raw_ds = xr.open_dataset(normalized_file, engine="netcdf4")
    return raw_ds, Path(normalized_file)


# %%
def derive_site_variables(raw_ds):
    derived = raw_ds.copy()

    # Convert native ERA5 variables to more directly usable units.
    tair_c = derived["t2m"] - 273.15
    dewpoint_c = derived["d2m"] - 273.15
    sst_c = derived["sst"] - 273.15
    skin_temperature_c = derived["skt"] - 273.15
    msl_hpa = derived["msl"] / 100.0
    sw_down = derived["ssrd"] / 3600.0
    lw_down = derived["strd"] / 3600.0
    wind_speed = np.sqrt(derived["u10"] ** 2 + derived["v10"] ** 2)

    # Calculate relative humidity from dewpoint and air temperature.
    # Source: https://bmcnoldy.earth.miami.edu/Humidity.html
    # See also NORSE2023_processing/src/inspect_NORSE_flux.py
    rh = 100.0 * (
        np.exp((17.625 * dewpoint_c) / (243.04 + dewpoint_c))
        / np.exp((17.625 * tair_c) / (243.04 + tair_c))
    )

    sw_down_7day = sw_down.rolling(valid_time=24 * 7, center=True, min_periods=1).mean()

    derived["wind_speed"] = wind_speed
    derived["air_temperature"] = tair_c
    derived["dewpoint_temperature"] = dewpoint_c
    derived["sea_surface_temperature"] = sst_c
    derived["skin_temperature"] = skin_temperature_c
    derived["barometric_pressure"] = msl_hpa
    derived["solar_radiation_downwards"] = sw_down
    derived["solar_radiation_downwards_7day"] = sw_down_7day
    derived["longwave_radiation_downwards"] = lw_down
    derived["relative_humidity"] = rh
    derived["wave_height"] = derived["swh"]
    derived["wave_period"] = derived["mwp"]
    derived["wave_direction"] = derived["mwd"]
    derived["total_precipitation"] = derived["tp"] * 1000.0                                                                                                                                                                                                    

    derived["wind_speed"].attrs["units"] = "m s-1"
    derived["air_temperature"].attrs["units"] = "degC"
    derived["dewpoint_temperature"].attrs["units"] = "degC"
    derived["sea_surface_temperature"].attrs["units"] = "degC"
    derived["barometric_pressure"].attrs["units"] = "hPa"
    derived["solar_radiation_downwards"].attrs["units"] = "W m-2"
    derived["longwave_radiation_downwards"].attrs["units"] = "W m-2"
    derived["relative_humidity"].attrs["units"] = "%"
    derived["wave_height"].attrs["units"] = "m"
    derived["wave_period"].attrs["units"] = "s"
    derived["wave_direction"].attrs["units"] = "degree true"
    derived["total_precipitation"].attrs["units"] = "mm hr-1"

    # Propagate GRIB_stepType from source variables (lost during arithmetic).
    grib_step_source = {
        "u10": "u10", "v10": "v10",
        "wind_speed": "u10",
        "air_temperature": "t2m",
        "dewpoint_temperature": "d2m",
        "sea_surface_temperature": "sst",
        "skin_temperature": "skt",
        "barometric_pressure": "msl",
        "solar_radiation_downwards": "ssrd",
        "solar_radiation_downwards_7day": "ssrd",
        "longwave_radiation_downwards": "strd",
        "relative_humidity": "t2m",
        "wave_height": "swh",
        "wave_period": "mwp",
        "wave_direction": "mwd",
        "total_precipitation": "tp",
    }
    for derived_var, source_var in grib_step_source.items():
        if "GRIB_stepType" in raw_ds[source_var].attrs:
            derived[derived_var].attrs["GRIB_stepType"] = raw_ds[source_var].attrs["GRIB_stepType"]

    keep_vars = [
        "u10",
        "v10",
        "wind_speed",
        "air_temperature",
        "sea_surface_temperature",
        "skin_temperature",
        "relative_humidity",
        "total_precipitation",
        "solar_radiation_downwards",
        "longwave_radiation_downwards",
        "barometric_pressure",
        "wave_height",
        "wave_period",
        "wave_direction",
    ]
    site_ds = derived[keep_vars]
    site_ds.attrs["site_name"] = site_name
    site_ds.attrs["site_longitude"] = float(derived["longitude"].values)
    site_ds.attrs["site_latitude"] = float(derived["latitude"].values)
    return site_ds


# %%
def save_dataset(ds, outfile):
    ds = ds.copy()
    now = dt.datetime.utcnow()
    ds.attrs["date_created"] = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    ds.attrs["history"] = f"{now.strftime('%Y-%m-%d')} ERA5_timeseries_extraction.py"
    ds.load()
    ds.to_netcdf(outfile)


# %%
ERA5_extraction_tool.tic()
output_file_met = out_path + 'ERA5_surface_' + site_name + '_' + startdate[:4] + '_' + enddate[:4] + '.nc'
print(f'Extracting ERA5 surface meteorological data for {site_name} for years {startdate[:4]} to {enddate[:4]}...')
print('View the progress here: https://cds.climate.copernicus.eu/requests')
try:
    ERA5_extraction_tool.get_timeseries(lon_pt, lat_pt, startdate, enddate, output_file_met)
    print(f"Successfully downloaded: {output_file_met}")
except Exception as e:
    print(f"Error downloading surface data: {e}")
ERA5_extraction_tool.toc()

# %% Derive variables and save processed dataset
processed_file = Path(out_path) / f'ERA5_surface_{site_name}_site_timeseries.nc'
raw_ds, normalized_file = open_timeseries_file(output_file_met)
site_ds = derive_site_variables(raw_ds)
save_dataset(site_ds, processed_file)
print(f'Saved processed dataset: {processed_file}')
