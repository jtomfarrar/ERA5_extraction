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
yrs = np.arange(2024,2025,1) # endpoint is not included
months = ['11', '12',],#['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12',],
# E-W valid range is -180, 180

lon0 = -161 # ASTRAL_big=80  # NORSE=3, WHOTS=-158
lat0 = 35 # ASTRAL_big=11  # NORSE=70, WHOTS=22.67
dlat = 20
dlon = 40
region_name = 'SAFARI' #'ASTRAL_big_2025'
region_name_waves = region_name + '_waves'
out_path = '../data/processed/'

# %%

for yr in yrs:
    ERA5_extraction_tool.tic()
    output_file_met = out_path + 'ERA5_surface_' + region_name + '_' + str(yr) +'.nc'
    display(f'Extracting ERA5 surface meteorological data for {region_name} for year {yr}...')
    display('View the progress here: https://cds.climate.copernicus.eu/live/queue')
    try:
        ERA5_extraction_tool.get_surface_vars(lon0, lat0, dlon, dlat, str(yr), months[0], output_file_met)
        print(f"Successfully downloaded: {output_file_met}")
    except Exception as e:
        print(f"Error downloading surface data: {e}")
    ERA5_extraction_tool.toc()
    time.sleep(5) # I am not sure this helps, but it seems like
                  # rapid repeated requests may cause it to bog down
                  # For some reason, the first 2 requests are quickly processed
                  # and the third one takes very long
    ERA5_extraction_tool.tic()
    output_file_waves = out_path + 'ERA5_surface_' + region_name_waves + '_' + str(yr) +'.nc'
    ERA5_extraction_tool.get_wave_vars(lon0, lat0, dlon, dlat, str(yr), months[0], output_file_waves)
    ERA5_extraction_tool.toc()


# %%
