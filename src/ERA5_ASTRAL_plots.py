# -*- coding: utf-8 -*-
"""
Make plots of ERA5 surface conditions at NORSE site

Modified from ERA5_NORSE_plots.py (from ERA5_plots repo) Aug 30 2024

@author: jtomfarrar
jfarrar@whoi.edu
"""
# %%
import os
from mpl_toolkits.basemap import Basemap
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mplt
#import nc_time_axis
import xarray as xr
import glob
from tqdm.contrib.concurrent import thread_map, process_map # allows parallel processing of movies
from tqdm import tqdm
# %%
# change to the directory where this script is located
home_dir = os.path.expanduser("~")
os.chdir(home_dir+'/Python/ERA5_extraction/src')
# %%
site_name = 'ASTRAL'#'Lofoten_Basin'#'Jan_Mayan'#'NORSE' #can be 'NTAS', 'WHOTS', 'Stratus', or 'Papa'

if site_name=='WHOTS':
    lon_pt = -158 # WHOTS=-158
    lat_pt = 22.67 # WHOTS=22.67
elif site_name=='NORSE':
    lon_pt = -6.1 #3
    lat_pt = 71 #70
elif site_name=='ASTRAL':
    lon_pt = 86 #3
    lat_pt = 12 #70
# %%
__figdir__ = '../img/'
savefig_args = {'bbox_inches':'tight', 'pad_inches':0.2}
savefig = False

movie_dir = __figdir__ + '/movie_frames_ASTRAL/'
# make directory if it doesn't exist
if not os.path.exists(movie_dir):
    os.makedirs(movie_dir)

ip = get_ipython() if 'get_ipython' in globals() else None
if ip is not None:
    ip.run_line_magic('matplotlib', 'ipympl')
    # ip.run_line_magic('matplotlib', 'qt5')
plt.rcParams['figure.figsize'] = (5,4)
plt.rcParams['figure.dpi'] = 100
plt.rcParams['savefig.dpi'] = 400

#Define path using the r prefix (which means raw string so that special character / should not be evaluated)
path = r"../data/processed/"

# %%
filename = path + 'ERA5_surface_' + site_name + '_big_2024.nc'
ERA = xr.open_dataset(filename)

# %%
def plot_map(ERA,tind,lev):
    sst = ERA.sst[tind,:,:]-273.15
    atmp = ERA.t2m[tind,:,:]-273.15
    U = ERA.u10[tind,:,:]
    V = ERA.v10[tind,:,:]
    msl = ERA.msl[tind,:,:]/100 # convert Pa to hPa (mb)
    sp = ERA.sp[tind,:,:]/100 # convert Pa to hPa (mb)
    lon = ERA.longitude
    lat = ERA.latitude
    lonmesh, latmesh = np.meshgrid(lon, lat)

    fig = plt.figure(figsize=(8,5))
    map = Basemap(**cyl_params)
    x,y = map(lonmesh,latmesh) # translate lat/lon to map coordinates
    map.drawcountries()
    #map.drawmapboundary(fill_color='aqua')
    map.fillcontinents(lake_color='aqua')
    map.contourf(x, y , atmp, cmap='coolwarm', levels=lev)
    map.drawcoastlines()
    map.drawparallels(range(-90, 90, 15),labels=[1,0,0,0]) #labels = [left,right,top,bottom]
    map.drawmeridians(range(0, 360, 15), labels=[0,0,0,1]) #  labels=[1,0,0,1]
    plt.title(time[tind].values)
    map.colorbar(mappable=None, location='right', size='5%', pad='2%', label='Air temp. ($^\circ$C)')
    xpt, ypt = map(lon_pt, lat_pt)
    map.plot(xpt, ypt, marker='D',color='m')
    # map.quiver(xpt,ypt,np.mean(u0),np.mean(v0),scale=10,scale_units='inches',color='k')
    skipx, skipy = 3, 3
    scale = 300 
    map.quiver(x[1:-1:skipy,1:-1:skipx],y[1:-1:skipy,1:-1:skipx],U[1:-1:skipy,1:-1:skipx],V[1:-1:skipy,1:-1:skipx],scale_units='width', scale = scale,color='k')


# %%
time = ERA.valid_time  # 'days since 1950-01-01 00:00:00'


#swh = ERA.swh[tind,:,:]

#############################
# %%
# Site map
#lcc_params={'projection':'lcc', 'lat_1':lat_pt-5,'lat_2':lat_pt+5,'lat_0':lat_pt,'lon_0':lon_pt,'width':5*10**6,'height':5*10**6, 'resolution':'h'}
lcc_params={'projection':'lcc', 'lat_1':65,'lat_2':70,'lat_0':70,'lon_0':-6,'llcrnrlat':59,'urcrnrlat':80,'llcrnrlon':-30,'urcrnrlon':70, 'resolution':'h'}
ortho_params = {'projection':'ortho','lat_0':lat_pt,'lon_0':lon_pt,'resolution':'l'}
dx=14
dy=15
cyl_params={'projection':'cyl', 'lat_1':lat_pt-5,'lat_2':lat_pt+5,'lat_0':lat_pt,'lon_0':lon_pt,'llcrnrlat':lat_pt-dy,'urcrnrlat':lat_pt+dy,'llcrnrlon':lon_pt-dx,'urcrnrlon':lon_pt+dx, 'resolution':'h'}


# %%
# find time index corresponding to 2023/11/15 00:00
tind = np.where(time==np.datetime64('2024-06-10T00:00:00'))[0][0]
lev = np.arange(20,33,1)
# lev = np.arange(1000,1020,1)

plot_map(ERA,tind,lev)

if savefig:
    plt.savefig(__figdir__+'_map',**savefig_args)



# %%
# now make a movie
# clear contents of movie_frames directory
files = glob.glob(movie_dir+'*')
for f in files:
    os.remove(f)

# %%
'''
for tind in range(0,len(time),2):
    print('Frame: ' + str(tind) ' of ' + str(len(time)))
    plot_map(ERA,tind)
    # 4 digit number for frame number
    plt.savefig(movie_dir+'NORSE_map_'+str(tind).zfill(4),**savefig_args)
    plt.close()
'''
# %%
# parallel version of the above loop
def plot_map_parallel(tind):
    plot_map(ERA,tind,lev)
    plt.savefig(movie_dir+'ASTRAL_map_'+str(tind).zfill(4),**savefig_args)
    plt.close()

# %%
# parallel version of the above loop
if __name__ == "__main__":
    # This will parallelize a for loop over loop_idx:
    tind = range(0,len(time))
    out = process_map(plot_map_parallel, tind)

# %%
# Use ffmpeg to generate the movie
import subprocess
fps = 24
command = [
    'ffmpeg',
    '-y',
    '-framerate', str(fps),  # Frame rate
    '-pattern_type', 'glob',  # Use glob pattern
    '-i', f'../img/movie_frames_ASTRAL/*.png',  # Input format with glob pattern for PNG files
    '-vf', "crop=trunc(iw/2)*2:trunc(ih/2)*2",  # Crop to even dimensions
    '-c:v', 'libx264',  # Codec: H.264
    '-pix_fmt', 'yuv420p',  # Pixel format
    '-crf', '17',  # Constant Rate Factor (quality), aiming for high quality
    '../img/ASTRAL.mp4'
]
subprocess.run(command)

# %%


