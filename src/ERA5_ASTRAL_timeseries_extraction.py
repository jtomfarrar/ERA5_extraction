# -*- coding: utf-8 -*-
"""
Created on Wed Jan 20 11:02:33 2021

@author: jtomf
"""
# %%
# change to the directory where this script is located
import os

home_dir = os.path.expanduser("~")
os.chdir(home_dir+'/Python/ERA5_plots_2024/src')

# %%

import ERA5_extraction_tool
import numpy as np
import time

# %%

# N, W, S, E valid range is 90, -180, -90, 180
# could use lon0=0 lat0=0 dlon=180 dlat=90
yrs = np.arange(2010,2025,1) # endpoint is not included
months = ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12',],
# E-W valid range is -180, 180


lon0 = -130.2 # Endurance_RCA
lat0 = 44.98 # Endurance_RCA
dlat = 1
dlon = 1
region_name = 'Endurance_RCA'#'SAFARI' #'ASTRAL_big_2025'
region_name_waves = region_name + '_waves'
out_path = '../data/processed/timeseries/' # this is where the extracted data will be saved
# create the output directory if it doesn't exist
if not os.path.exists(out_path):
    os.makedirs(out_path)
# %%
'''
for yr in yrs:
    for month in months[0]:
        ERA5_extraction_tool.tic()
        output_file_met = out_path + 'ERA5_surface_' + region_name + '_' + str(yr) + '_' + month +'.nc'
        display(f'Extracting ERA5 surface meteorological data for {region_name} for year {yr} month {month}...')
        display('View the progress here: https://cds.climate.copernicus.eu/requests')
        try:
            ERA5_extraction_tool.get_surface_vars(lon0, lat0, dlon, dlat, str(yr), month, output_file_met)
            print(f"Successfully downloaded: {output_file_met}")
        except Exception as e:
            print(f"Error downloading surface data: {e}")
        ERA5_extraction_tool.toc()
        time.sleep(5) # I am not sure this helps, but it seems like
                    # rapid repeated requests may cause it to bog down
                    # For some reason, the first 2 requests are quickly processed
                    # and the third one takes very long
        ERA5_extraction_tool.tic()
        output_file_waves = out_path + 'ERA5_surface_' + region_name_waves + '_' + str(yr) + '_' + month +'.nc'
        ERA5_extraction_tool.get_wave_vars(lon0, lat0, dlon, dlat, str(yr), month, output_file_waves)
        ERA5_extraction_tool.toc()
'''

# %%
# Should try this way
# https://cds.climate.copernicus.eu/datasets/reanalysis-era5-single-levels-timeseries?tab=overview
# Please note that a dedicated catalogue entry for this dataset, post-processed and stored in Analysis Ready Cloud Optimized (ARCO) format (Zarr), is available for optimised time-series retrievals (i.e. for retrieving data from selected variables for a single point over an extended period of time in an efficient way). You can discover it [here](https://cds.climate.copernicus.eu/datasets/reanalysis-era5-single-levels-timeseries?tab=overview)
'''
import cdsapi

dataset = "reanalysis-era5-single-levels-timeseries"
request = {
    "variable": [
        "2m_dewpoint_temperature",
        "mean_sea_level_pressure",
        "surface_pressure",
        "surface_solar_radiation_downwards",
        "sea_surface_temperature",
        "surface_thermal_radiation_downwards",
        "2m_temperature",
        "total_precipitation",
        "10m_u_component_of_wind",
        "10m_v_component_of_wind",
        "mean_wave_direction",
        "mean_wave_period",
        "significant_height_of_combined_wind_waves_and_swell"
    ],
    "location": {"longitude": 135, "latitude": 10},
    "date": ["2020-01-01/2026-03-04"],
    "data_format": "netcdf"
}

client = cdsapi.Client()
client.retrieve(dataset, request).download()
'''
# %%
startdate = '2010-01-01'
enddate = '2024-12-31'
ERA5_extraction_tool.tic()
output_file_met = out_path + 'ERA5_surface_' + region_name + '_' + startdate[:4] + '_' + enddate[:4] +'.nc'
display(f'Extracting ERA5 surface meteorological data for {region_name} for years {startdate[:4]} to {enddate[:4]}...')
display('View the progress here: https://cds.climate.copernicus.eu/requests')
try:    
    ERA5_extraction_tool.get_timeseries(lon0, lat0, startdate, enddate, output_file_met)
    print(f"Successfully downloaded: {output_file_met}")
except Exception as e:    print(f"Error downloading surface data: {e}")
ERA5_extraction_tool.toc()




