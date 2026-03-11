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
os.chdir(home_dir+'/Python/ERA5_plots_2024/src')
# %%
site_name = 'SAFARI'#'Lofoten_Basin'#'Jan_Mayan'#'NORSE' #can be 'NTAS', 'WHOTS', 'Stratus', or 'Papa'

if site_name=='WHOTS':
    lon_pt = -158 # WHOTS=-158
    lat_pt = 22.67 # WHOTS=22.67
elif site_name=='NORSE':
    lon_pt = -6.1 #3
    lat_pt = 71 #70
elif site_name=='ASTRAL':
    lon_pt = 86 #3
    lat_pt = 12 #70
elif site_name=='SAFARI':
    lon_pt = -161 
    lat_pt = 35
# %%
__figdir__ = '../img/'
savefig_args = {'bbox_inches':'tight', 'pad_inches':0.2}
savefig = True

movie_dir = __figdir__ + '/movie_frames/'
# make directory if it doesn't exist
if not os.path.exists(movie_dir):
    os.makedirs(movie_dir)

%matplotlib widget
# %matplotlib qt5
plt.rcParams['figure.figsize'] = (5,4)
plt.rcParams['figure.dpi'] = 100
plt.rcParams['savefig.dpi'] = 400

#Define path using the r prefix (which means raw string so that special character / should not be evaluated)
path = r"../data/processed/"

# %%
filename = path + 'ERA5_surface_' + site_name + '_2024.nc'
ERA = xr.open_dataset(filename,engine='netcdf4')

filename_wave = path + 'ERA5_surface_' + site_name + '_waves_2024.nc'
ERA_waves = xr.open_dataset(filename_wave)



# %%
def plot_map(ERA,tind,lev):
    sst = ERA.sst[tind,:,:]-273.15
    atmp = ERA.t2m[tind,:,:]-273.15
    U = ERA.u10[tind,:,:]
    V = ERA.v10[tind,:,:]
    sp = ERA.sp[tind,:,:]/100 # convert Pa to hPa (mb)
    msl = ERA.msl[tind,:,:]/100 # convert Pa to hPa (mb)
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
    skipx, skipy = 5, 5
    scale = 300 
    q = map.quiver(x[1:-1:skipy,1:-1:skipx],y[1:-1:skipy,1:-1:skipx],U[1:-1:skipy,1:-1:skipx],V[1:-1:skipy,1:-1:skipx],scale_units='width', scale = scale,color='k')
    qk = plt.quiverkey(q, 0.3, 0.06, 10, '10 m/s', labelpos='E', coordinates='figure')
    time0 = ERA.valid_time[tind].values
    # convert time to dtype='datetime64[ns]'
    # time = np.datetime64(time)
# %%
def contour_SLP(ERA,tind,lev):
    sst = ERA.sst[tind,:,:]-273.15
    atmp = ERA.t2m[tind,:,:]-273.15
    U = ERA.u10[tind,:,:]
    V = ERA.v10[tind,:,:]
    sp = ERA.sp[tind,:,:]/100 # convert Pa to hPa (mb)
    msl = ERA.msl[tind,:,:]/100 # convert Pa to hPa (mb)
    lon = ERA.longitude
    lat = ERA.latitude
    lonmesh, latmesh = np.meshgrid(lon, lat)

    fig = plt.figure(figsize=(8,5))
    map = Basemap(**cyl_params)
    x,y = map(lonmesh,latmesh) # translate lat/lon to map coordinates
    map.drawcountries()
    #map.drawmapboundary(fill_color='aqua')
    map.fillcontinents(lake_color='aqua')
    C1 = map.contourf(x, y , msl, cmap='turbo', levels=lev)
    #C2 = map.contour(x, y , msl, levels=lev, colors='k', linewidths=0.5)
    #cb = plt.clabel(C2, lev, inline=True, fmt='%1.0f', fontsize=10)
    #[txt.set_bbox(dict(boxstyle='square,pad=0',fc='red')) for txt in cb]
    map.drawcoastlines()
    map.drawparallels(range(-90, 90, 15),labels=[1,0,0,0]) #labels = [left,right,top,bottom]
    map.drawmeridians(range(0, 360, 15), labels=[0,0,0,1]) #  labels=[1,0,0,1]
    plt.title(time[tind].values)
    map.colorbar(C1, location='right', size='5%', pad='2%', label='SLP (mb)') #label='Air temp. ($^\circ$C)')
    xpt, ypt = map(lon_pt, lat_pt)
    map.plot(xpt, ypt, marker='D',color='m')
    # map.quiver(xpt,ypt,np.mean(u0),np.mean(v0),scale=10,scale_units='inches',color='k')
    skipx, skipy = 5, 5
    scale = 300 
    q = map.quiver(x[1:-1:skipy,1:-1:skipx],y[1:-1:skipy,1:-1:skipx],U[1:-1:skipy,1:-1:skipx],V[1:-1:skipy,1:-1:skipx],scale_units='width', scale = scale,color='k')
    qk = plt.quiverkey(q, 0.3, 0.06, 10, '10 m/s', labelpos='E', coordinates='figure')
    time0 = ERA.valid_time[tind].values

# %%
def plot_SST(ERA,tind,lev):
    sst = ERA.sst[tind,:,:]-273.15
    atmp = ERA.t2m[tind,:,:]-273.15
    U = ERA.u10[tind,:,:]
    V = ERA.v10[tind,:,:]
    sp = ERA.sp[tind,:,:]/100 # convert Pa to hPa (mb)
    msl = ERA.msl[tind,:,:]/100 # convert Pa to hPa (mb)
    lon = ERA.longitude
    lat = ERA.latitude
    lonmesh, latmesh = np.meshgrid(lon, lat)

    fig = plt.figure(figsize=(8,5))
    map = Basemap(**cyl_params)
    x,y = map(lonmesh,latmesh) # translate lat/lon to map coordinates
    map.drawcountries()
    #map.drawmapboundary(fill_color='aqua')
    map.fillcontinents(lake_color='aqua')
    C1 = map.contourf(x, y , sst, cmap='coolwarm', levels=lev)
    map.drawcoastlines()
    map.drawparallels(range(-90, 90, 15),labels=[1,0,0,0]) #labels = [left,right,top,bottom]
    map.drawmeridians(range(0, 360, 15), labels=[0,0,0,1]) #  labels=[1,0,0,1]
    plt.title(time[tind].values)
    map.colorbar(C1, location='right', size='5%', pad='2%', label='SST ($^\circ$C)') #label='Air temp. ($^\circ$C)')
    xpt, ypt = map(lon_pt, lat_pt)
    map.plot(xpt, ypt, marker='D',color='m')
    skipx, skipy = 5, 5
    scale = 300 
    q = map.quiver(x[1:-1:skipy,1:-1:skipx],y[1:-1:skipy,1:-1:skipx],U[1:-1:skipy,1:-1:skipx],V[1:-1:skipy,1:-1:skipx],scale_units='width', scale = scale,color='k')
    qk = plt.quiverkey(q, 0.3, 0.06, 10, '10 m/s', labelpos='E', coordinates='figure')
    time0 = ERA.valid_time[tind].values

# %%
def plot_SWH(ERA,tind,lev):
    U = ERA.u10[tind,:,:]
    V = ERA.v10[tind,:,:]
    lon = ERA.longitude
    lat = ERA.latitude
    lonmesh, latmesh = np.meshgrid(lon, lat)
    swh = ERA_waves.swh[tind,:,:]
    lonw = ERA_waves.longitude
    latw = ERA_waves.latitude
    lonmeshw, latmeshw = np.meshgrid(lonw, latw)

    fig = plt.figure(figsize=(8,5))
    map = Basemap(**cyl_params)
    xw,yw = map(lonmeshw,latmeshw) # translate lat/lon to map coordinates
    x,y = map(lonmesh,latmesh) # translate lat/lon to map coordinates
    map.drawcountries()
    #map.drawmapboundary(fill_color='aqua')
    map.fillcontinents(lake_color='aqua')
    C1 = map.contourf(xw, yw , swh, cmap='coolwarm', levels=lev)
    map.drawcoastlines()
    map.drawparallels(range(-90, 90, 15),labels=[1,0,0,0]) #labels = [left,right,top,bottom]
    map.drawmeridians(range(0, 360, 15), labels=[0,0,0,1]) #  labels=[1,0,0,1]
    plt.title(time[tind].values)
    map.colorbar(C1, location='right', size='5%', pad='2%', label='SWH (m)') #label='Air temp. ($^\circ$C)')
    xpt, ypt = map(lon_pt, lat_pt)
    map.plot(xpt, ypt, marker='D',color='m')
    skipx, skipy = 5, 5
    scale = 300 
    q = map.quiver(x[1:-1:skipy,1:-1:skipx],y[1:-1:skipy,1:-1:skipx],U[1:-1:skipy,1:-1:skipx],V[1:-1:skipy,1:-1:skipx],scale_units='width', scale = scale,color='k')
    qk = plt.quiverkey(q, 0.3, 0.06, 10, '10 m/s', labelpos='E', coordinates='figure')
    time0 = ERA.valid_time[tind].values

# %%

# %%
time = ERA.valid_time  # 'days since 1950-01-01 00:00:00'


#swh = ERA.swh[tind,:,:]

#############################
# %%
# Site map
#lcc_params={'projection':'lcc', 'lat_1':lat_pt-5,'lat_2':lat_pt+5,'lat_0':lat_pt,'lon_0':lon_pt,'width':5*10**6,'height':5*10**6, 'resolution':'h'}
lcc_params={'projection':'lcc', 'lat_1':65,'lat_2':70,'lat_0':70,'lon_0':-6,'llcrnrlat':59,'urcrnrlat':80,'llcrnrlon':-30,'urcrnrlon':70, 'resolution':'h'}
ortho_params = {'projection':'ortho','lat_0':lat_pt,'lon_0':lon_pt,'resolution':'l'}
dx=40
dy=20
cyl_params={'projection':'cyl', 'lat_1':lat_pt-5,'lat_2':lat_pt+5,'lat_0':lat_pt,'lon_0':lon_pt,'llcrnrlat':lat_pt-dy,'urcrnrlat':lat_pt+dy,'llcrnrlon':lon_pt-dx,'urcrnrlon':lon_pt+dx, 'resolution':'h'}


# %%
# find time index corresponding to 2023/11/15 00:00
tind = np.where(time==np.datetime64('2024-12-20T02:00:00'))[0][0]

# %%
var ='slp' #'atmp' #'slp' #'sst' #'swh'
if var == 'atmp':
    lev = np.arange(3,29,1) # good for temperature
    plot_map(ERA,tind,lev)
    if savefig:
        plt.savefig(__figdir__+'SAFARI_ATMP_map',**savefig_args)
elif var == 'slp':
    lev = np.arange(940,1020,2)
    contour_SLP(ERA,tind,lev)
    if savefig:
        plt.savefig(__figdir__+'SAFARI_SLP_map',**savefig_args)
elif var == 'sst':
    lev = np.arange(5,30,.5)
    plot_SST(ERA,tind,lev)
    if savefig:
        plt.savefig(__figdir__+'SAFARI_SST_map',**savefig_args)
elif var == 'swh':
    lev = np.arange(-.1,12,.1)
    plot_SWH(ERA,tind,lev)
    if savefig:
        plt.savefig(__figdir__+'SAFARI_SWH_map',**savefig_args)

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
    plt.clf()
    if var == 'atmp': plot_map(ERA,tind,lev)
    elif var == 'slp': contour_SLP(ERA,tind,lev)
    elif var == 'sst': plot_SST(ERA,tind,lev)
    elif var == 'swh': plot_SWH(ERA,tind,lev)
    # Plot WG positions

    plt.legend()
    plt.savefig(movie_dir+'SAFARI_map_'+str(tind).zfill(4),**savefig_args)
    plt.close()


# parallel version of the above loop
if __name__ == "__main__":
    # This will parallelize a for loop over loop_idx:
    tind = range(0,int(len(time)))
    out = process_map(plot_map_parallel, tind)

# %%
# Use ffmpeg to generate the movie
import subprocess
fps = 18
command = [
    'ffmpeg',
    '-y',
    '-framerate', str(fps),  # Frame rate
    '-pattern_type', 'glob',  # Use glob pattern
    '-i', f'../img/movie_frames/*.png',  # Input format with glob pattern for PNG files
    '-vf', "crop=trunc(iw/2)*2:trunc(ih/2)*2",  # Crop to even dimensions
    '-c:v', 'libx264',  # Codec: H.264
    '-pix_fmt', 'yuv420p',  # Pixel format
    '-crf', '17',  # Constant Rate Factor (quality), aiming for high quality
    '../img/SAFARI_'+var+'_out.mp4'
]
subprocess.run(command)

# %%
# Find the minimum msl at each time
min_msl = ERA.msl.min(dim=['latitude','longitude'])/100
# Find max wind speed at each time
max_wind = np.sqrt(ERA.u10**2 + ERA.v10**2).max(dim=['latitude','longitude'])
fig, axs = plt.subplots(2, 1, sharex=True)
axs[0].plot(time,min_msl)
axs[0].title.set_text('Minimum SL pressure')
axs[0].set_ylabel('Pressure (mbar)')
axs[0].grid()

axs[1].plot(time,max_wind)
axs[1].plot(time,max_wind*0+33,'r--')
axs[1].title.set_text('Maximum wind speed')
axs[1].set_ylabel('Wind speed (m/s)')
axs[1].grid()

fig.autofmt_xdate()

plt.savefig(__figdir__+'ASTRAL_min_msl_max_wind',**savefig_args)


# %%
