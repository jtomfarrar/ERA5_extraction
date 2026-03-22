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
site_name = 'RAMA_12N'#'SAFARI'

if site_name=="RAMA_12N":
    lon_pt = 88.5  # 88 deg 30.0'E
    lat_pt = 12.0  # 12 deg 00.0'N
    startdate = '2000-01-01'
    enddate = '2026-01-01'
elif site_name=="Endurance_RCA":
    lon_pt = -130.2  # 130 deg 12.0'W
    lat_pt = 44.98   # 44 deg 58.8'N
    startdate = '2000-01-01'
    enddate = '2026-01-01'
elif site_name=='SAFARI':
    lon_pt = -161 
    lat_pt = 35
    startdate = '2000-01-01'
    enddate = '2026-03-21'

out_path = '../data/processed/timeseries/' # this is where the extracted data will be saved
# create the output directory if it doesn't exist
if not os.path.exists(out_path):
    os.makedirs(out_path)

# %%

ERA5_extraction_tool.tic()
output_file_met = out_path + 'ERA5_surface_' + site_name + '_' + startdate[:4] + '_' + enddate[:4] +'.nc'
display(f'Extracting ERA5 surface meteorological data for {site_name} for years {startdate[:4]} to {enddate[:4]}...')
display('View the progress here: https://cds.climate.copernicus.eu/requests')
try:    
    ERA5_extraction_tool.get_timeseries(lon_pt, lat_pt, startdate, enddate, output_file_met)
    print(f"Successfully downloaded: {output_file_met}")
except Exception as e:    print(f"Error downloading surface data: {e}")
ERA5_extraction_tool.toc()




