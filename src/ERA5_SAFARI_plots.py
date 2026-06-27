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
site_name = 'SAFARI_2025_2026'#'SAFARI'#'Lofoten_Basin'#'Jan_Mayan'#'NORSE' #can be 'NTAS', 'WHOTS', 'Stratus', or 'Papa'
var ='atmp' #'atmp' #'slp' #'sst' #'swh' #'tcwv' #'ivt' #'vimdf' #'evap' #'emp'

if site_name=='WHOTS':
    lon0 = -158
    lat0 = 22.67
    lon_pt = lon0 # WHOTS=-158
    lat_pt = lat0 # WHOTS=22.67
    suffix = ''
    dx = 40
    dy = 20
    map_resolution = 'h'
    plot_time = np.datetime64('2026-01-15T00:00:00')
    if var == 'slp':
        lev = np.arange(940,1020,2)
elif site_name=='NORSE':
    lon0 = -6.1
    lat0 = 71
    lon_pt = lon0 #3
    lat_pt = lat0 #70
    suffix = ''
    dx = 40
    dy = 20
    map_resolution = 'h'
    plot_time = np.datetime64('2026-01-15T00:00:00')
    if var == 'slp':
        lev = np.arange(940,1020,2)
elif site_name=='ASTRAL':
    lon0 = 86
    lat0 = 12
    lon_pt = lon0 #3
    lat_pt = lat0 #70
    suffix = ''
    dx = 40
    dy = 20
    map_resolution = 'h'
    plot_time = np.datetime64('2026-01-15T00:00:00')
    if var == 'slp':
        lev = np.arange(940,1020,2)
elif site_name=='SAFARI':
    lon0 = -161
    lat0 = 35
    lon_pt = lon0
    lat_pt = lat0
    suffix = ''
    dx = 40
    dy = 20
    map_resolution = 'h'
    plot_time = np.datetime64('2026-01-15T00:00:00')
    if var == 'slp':
        lev = np.arange(940,1020,2)
elif site_name=='SAFARI_2025_2026':
    lon0 = -161
    lat0 = 35
    lon_pt = -158
    lat_pt = 33.44
    suffix = '_202510_202606'
    dx = 48
    dy = 25
    map_resolution = 'l'
    plot_time = np.datetime64('2026-01-15T00:00:00')
    if var == 'slp':
        lev = np.arange(960,1030,3)
else:
    raise ValueError(f'No site configuration found for {site_name}')
# %%
__figdir__ = '../img/'
savefig_args = {'bbox_inches':'tight', 'pad_inches':0.2}
savefig = True

movie_dir = __figdir__ + 'movie_frames_' + site_name + '_' + var + '/'
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

filename = path + 'ERA5_surface_' + site_name + suffix + '.nc'
ERA = xr.open_dataset(filename,engine='netcdf4')

if var == 'swh':
    filename_wave = path + 'ERA5_surface_' + site_name + '_waves' + suffix + '.nc'
    ERA_waves = xr.open_dataset(filename_wave,engine='netcdf4')
elif var in ['tcwv','ivt','vimdf']:
    filename_moisture = path + 'ERA5_surface_' + site_name + '_moisture' + suffix + '.nc'
    ERA_moisture = xr.open_dataset(filename_moisture,engine='netcdf4')
elif var in ['evap','emp']:
    filename_fluxes = path + 'ERA5_surface_' + site_name + '_fluxes' + suffix + '.nc'
    ERA_fluxes = xr.open_dataset(filename_fluxes,engine='netcdf4')
    filename_moisture = path + 'ERA5_surface_' + site_name + '_moisture' + suffix + '.nc'
    ERA_moisture = xr.open_dataset(filename_moisture,engine='netcdf4')



# %%
def plot_map(ERA,tind,lev):
    atmp = ERA.t2m[tind,:,:]-273.15
    U = ERA.u10[tind,:,:]
    V = ERA.v10[tind,:,:]
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
    skipx, skipy = 8, 8
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
    skipx, skipy = 8, 8
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
    skipx, skipy = 8, 8
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
    time0 = ERA.valid_time[tind]
    swh = ERA_waves.swh.sel(valid_time=time0, method='nearest')
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
    skipx, skipy = 8, 8
    scale = 300 
    q = map.quiver(x[1:-1:skipy,1:-1:skipx],y[1:-1:skipy,1:-1:skipx],U[1:-1:skipy,1:-1:skipx],V[1:-1:skipy,1:-1:skipx],scale_units='width', scale = scale,color='k')
    qk = plt.quiverkey(q, 0.3, 0.06, 10, '10 m/s', labelpos='E', coordinates='figure')

# %%
def plot_TCWV(ERA_moisture,tind,lev):
    time0 = ERA_moisture.valid_time[tind]
    tcwv = ERA_moisture.tcwv.sel(valid_time=time0, method='nearest')
    U = ERA_moisture.viwve.sel(valid_time=time0, method='nearest')
    V = ERA_moisture.viwvn.sel(valid_time=time0, method='nearest')
    lon = ERA_moisture.longitude
    lat = ERA_moisture.latitude
    lonmesh, latmesh = np.meshgrid(lon, lat)

    fig = plt.figure(figsize=(8,5))
    map = Basemap(**cyl_params)
    x,y = map(lonmesh,latmesh) # translate lat/lon to map coordinates
    map.drawcountries()
    #map.drawmapboundary(fill_color='aqua')
    map.fillcontinents(lake_color='aqua')
    C1 = map.contourf(x, y , tcwv, cmap='YlGnBu', levels=lev)
    map.drawcoastlines()
    map.drawparallels(range(-90, 90, 15),labels=[1,0,0,0]) #labels = [left,right,top,bottom]
    map.drawmeridians(range(0, 360, 15), labels=[0,0,0,1]) #  labels=[1,0,0,1]
    plt.title(time0.values)
    map.colorbar(C1, location='right', size='5%', pad='2%', label='TCWV (kg m$^{-2}$)')
    xpt, ypt = map(lon_pt, lat_pt)
    map.plot(xpt, ypt, marker='D',color='m')
    skipx, skipy = 8, 8
    scale = 10000
    q = map.quiver(x[1:-1:skipy,1:-1:skipx],y[1:-1:skipy,1:-1:skipx],U[1:-1:skipy,1:-1:skipx],V[1:-1:skipy,1:-1:skipx],scale_units='width', scale = scale,color='k')
    qk = plt.quiverkey(q, 0.3, 0.06, 250, '250 kg m$^{-1}$ s$^{-1}$', labelpos='E', coordinates='figure')

# %%
def plot_IVT(ERA_moisture,tind,lev):
    time0 = ERA_moisture.valid_time[tind]
    U = ERA_moisture.viwve.sel(valid_time=time0, method='nearest')
    V = ERA_moisture.viwvn.sel(valid_time=time0, method='nearest')
    ivt = np.sqrt(U**2 + V**2)
    lon = ERA_moisture.longitude
    lat = ERA_moisture.latitude
    lonmesh, latmesh = np.meshgrid(lon, lat)

    fig = plt.figure(figsize=(8,5))
    map = Basemap(**cyl_params)
    x,y = map(lonmesh,latmesh) # translate lat/lon to map coordinates
    map.drawcountries()
    #map.drawmapboundary(fill_color='aqua')
    map.fillcontinents(lake_color='aqua')
    C1 = map.contourf(x, y , ivt, cmap='YlGnBu', levels=lev, extend='max')
    map.drawcoastlines()
    map.drawparallels(range(-90, 90, 15),labels=[1,0,0,0]) #labels = [left,right,top,bottom]
    map.drawmeridians(range(0, 360, 15), labels=[0,0,0,1]) #  labels=[1,0,0,1]
    plt.title(time0.values)
    map.colorbar(C1, location='right', size='5%', pad='2%', label='IVT (kg m$^{-1}$ s$^{-1}$)')
    xpt, ypt = map(lon_pt, lat_pt)
    map.plot(xpt, ypt, marker='D',color='m')
    skipx, skipy = 8, 8
    scale = 10000
    q = map.quiver(x[1:-1:skipy,1:-1:skipx],y[1:-1:skipy,1:-1:skipx],U[1:-1:skipy,1:-1:skipx],V[1:-1:skipy,1:-1:skipx],scale_units='width', scale = scale,color='k')
    qk = plt.quiverkey(q, 0.3, 0.06, 250, '250 kg m$^{-1}$ s$^{-1}$', labelpos='E', coordinates='figure')

# %%
def plot_VIMDF(ERA_moisture,tind,lev):
    time0 = ERA_moisture.valid_time[tind]
    vimdf = ERA_moisture.vimdf.sel(valid_time=time0, method='nearest') * 86400
    U = ERA_moisture.viwve.sel(valid_time=time0, method='nearest')
    V = ERA_moisture.viwvn.sel(valid_time=time0, method='nearest')
    lon = ERA_moisture.longitude
    lat = ERA_moisture.latitude
    lonmesh, latmesh = np.meshgrid(lon, lat)

    fig = plt.figure(figsize=(8,5))
    map = Basemap(**cyl_params)
    x,y = map(lonmesh,latmesh) # translate lat/lon to map coordinates
    map.drawcountries()
    #map.drawmapboundary(fill_color='aqua')
    map.fillcontinents(lake_color='aqua')
    C1 = map.contourf(x, y , vimdf, cmap='RdBu_r', levels=lev, extend='both')
    map.drawcoastlines()
    map.drawparallels(range(-90, 90, 15),labels=[1,0,0,0]) #labels = [left,right,top,bottom]
    map.drawmeridians(range(0, 360, 15), labels=[0,0,0,1]) #  labels=[1,0,0,1]
    plt.title(time0.values)
    map.colorbar(C1, location='right', size='5%', pad='2%', label='Moisture flux divergence (kg m$^{-2}$ day$^{-1}$)')
    xpt, ypt = map(lon_pt, lat_pt)
    map.plot(xpt, ypt, marker='D',color='m')
    skipx, skipy = 8, 8
    scale = 10000
    q = map.quiver(x[1:-1:skipy,1:-1:skipx],y[1:-1:skipy,1:-1:skipx],U[1:-1:skipy,1:-1:skipx],V[1:-1:skipy,1:-1:skipx],scale_units='width', scale = scale,color='k')
    qk = plt.quiverkey(q, 0.3, 0.06, 250, '250 kg m$^{-1}$ s$^{-1}$', labelpos='E', coordinates='figure')

# %%
def plot_evap_rate(ERA_fluxes,tind,lev):
    time0 = ERA_fluxes.valid_time[tind]
    evap_rate = -ERA_fluxes.e.sel(valid_time=time0, method='nearest') * 1000 * 24
    U = ERA_moisture.viwve.sel(valid_time=time0, method='nearest')
    V = ERA_moisture.viwvn.sel(valid_time=time0, method='nearest')
    lon = ERA_fluxes.longitude
    lat = ERA_fluxes.latitude
    lonmesh, latmesh = np.meshgrid(lon, lat)

    fig = plt.figure(figsize=(8,5))
    map = Basemap(**cyl_params)
    x,y = map(lonmesh,latmesh) # translate lat/lon to map coordinates
    map.drawcountries()
    #map.drawmapboundary(fill_color='aqua')
    map.fillcontinents(lake_color='aqua')
    C1 = map.contourf(x, y , evap_rate, cmap='YlGnBu', levels=lev, extend='max')
    map.drawcoastlines()
    map.drawparallels(range(-90, 90, 15),labels=[1,0,0,0]) #labels = [left,right,top,bottom]
    map.drawmeridians(range(0, 360, 15), labels=[0,0,0,1]) #  labels=[1,0,0,1]
    plt.title(time0.values)
    map.colorbar(C1, location='right', size='5%', pad='2%', label='Evaporation rate (mm day$^{-1}$)')
    xpt, ypt = map(lon_pt, lat_pt)
    map.plot(xpt, ypt, marker='D',color='m')
    skipx, skipy = 8, 8
    scale = 10000
    q = map.quiver(x[1:-1:skipy,1:-1:skipx],y[1:-1:skipy,1:-1:skipx],U[1:-1:skipy,1:-1:skipx],V[1:-1:skipy,1:-1:skipx],scale_units='width', scale = scale,color='k')
    qk = plt.quiverkey(q, 0.3, 0.06, 250, '250 kg m$^{-1}$ s$^{-1}$', labelpos='E', coordinates='figure')

# %%
def plot_EMP(ERA_fluxes,tind,lev):
    time0 = ERA_fluxes.valid_time[tind]
    evap_rate = -ERA_fluxes.e.sel(valid_time=time0, method='nearest') * 1000 * 24
    precip_rate = ERA_fluxes.tp.sel(valid_time=time0, method='nearest') * 1000 * 24
    emp = evap_rate - precip_rate
    U = ERA_moisture.viwve.sel(valid_time=time0, method='nearest')
    V = ERA_moisture.viwvn.sel(valid_time=time0, method='nearest')
    lon = ERA_fluxes.longitude
    lat = ERA_fluxes.latitude
    lonmesh, latmesh = np.meshgrid(lon, lat)

    fig = plt.figure(figsize=(8,5))
    map = Basemap(**cyl_params)
    x,y = map(lonmesh,latmesh) # translate lat/lon to map coordinates
    map.drawcountries()
    #map.drawmapboundary(fill_color='aqua')
    map.fillcontinents(lake_color='aqua')
    C1 = map.contourf(x, y , emp, cmap='RdBu_r', levels=lev, extend='both')
    map.drawcoastlines()
    map.drawparallels(range(-90, 90, 15),labels=[1,0,0,0]) #labels = [left,right,top,bottom]
    map.drawmeridians(range(0, 360, 15), labels=[0,0,0,1]) #  labels=[1,0,0,1]
    plt.title(time0.values)
    map.colorbar(C1, location='right', size='5%', pad='2%', label='E - P (mm day$^{-1}$)')
    xpt, ypt = map(lon_pt, lat_pt)
    map.plot(xpt, ypt, marker='D',color='m')
    skipx, skipy = 8, 8
    scale = 10000
    q = map.quiver(x[1:-1:skipy,1:-1:skipx],y[1:-1:skipy,1:-1:skipx],U[1:-1:skipy,1:-1:skipx],V[1:-1:skipy,1:-1:skipx],scale_units='width', scale = scale,color='k')
    qk = plt.quiverkey(q, 0.3, 0.06, 250, '250 kg m$^{-1}$ s$^{-1}$', labelpos='E', coordinates='figure')

# %%

# %%
if var in ['tcwv','ivt','vimdf']:
    time = ERA_moisture.valid_time
elif var in ['evap','emp']:
    ERA_fluxes = ERA_fluxes.sel(valid_time=ERA_moisture.valid_time)
    time = ERA_fluxes.valid_time
else:
    time = ERA.valid_time  # 'days since 1950-01-01 00:00:00'


#swh = ERA.swh[tind,:,:]

#############################
# %%
# Site map
#lcc_params={'projection':'lcc', 'lat_1':lat0-5,'lat_2':lat0+5,'lat_0':lat0,'lon_0':lon0,'width':5*10**6,'height':5*10**6, 'resolution':'h'}
lcc_params={'projection':'lcc', 'lat_1':lat0-5,'lat_2':lat0+5,'lat_0':lat0,'lon_0':lon0,'llcrnrlat':lat0-dy,'urcrnrlat':lat0+dy,'llcrnrlon':lon0-dx,'urcrnrlon':lon0+dx, 'resolution':map_resolution}
ortho_params = {'projection':'ortho','lat_0':lat0,'lon_0':lon0,'resolution':map_resolution}
cyl_params={'projection':'cyl', 'lat_1':lat0-5,'lat_2':lat0+5,'lat_0':lat0,'lon_0':lon0,'llcrnrlat':lat0-dy,'urcrnrlat':lat0+dy,'llcrnrlon':lon0-dx,'urcrnrlon':lon0+dx, 'resolution':map_resolution}


# %%
# find time index corresponding to the selected plot time
tind = np.where(time==plot_time)[0][0]

# %%
if var == 'atmp':
    lev = np.arange(3,29,1) # good for temperature
    plot_map(ERA,tind,lev)
    if savefig:
        plt.savefig(__figdir__ + site_name + '_ATMP_map',**savefig_args)
elif var == 'slp':
    contour_SLP(ERA,tind,lev)
    if savefig:
        plt.savefig(__figdir__ + site_name + '_SLP_map',**savefig_args)
elif var == 'sst':
    lev = np.arange(5,30,.5)
    plot_SST(ERA,tind,lev)
    if savefig:
        plt.savefig(__figdir__ + site_name + '_SST_map',**savefig_args)
elif var == 'swh':
    lev = np.arange(-.2,10.2,.2)
    plot_SWH(ERA,tind,lev)
    if savefig:
        plt.savefig(__figdir__ + site_name + '_SWH_map',**savefig_args)
elif var == 'tcwv':
    lev = np.arange(0,72,2)
    plot_TCWV(ERA_moisture,tind,lev)
    if savefig:
        plt.savefig(__figdir__ + site_name + '_TCWV_map',**savefig_args)
elif var == 'ivt':
    lev = np.arange(0,1000,50)
    plot_IVT(ERA_moisture,tind,lev)
    if savefig:
        plt.savefig(__figdir__ + site_name + '_IVT_map',**savefig_args)
elif var == 'vimdf':
    lev = np.arange(-40,42,2)
    plot_VIMDF(ERA_moisture,tind,lev)
    if savefig:
        plt.savefig(__figdir__ + site_name + '_VIMDF_map',**savefig_args)
elif var == 'evap':
    lev = np.arange(0,25,1)
    plot_evap_rate(ERA_fluxes,tind,lev)
    if savefig:
        plt.savefig(__figdir__ + site_name + '_EVAP_map',**savefig_args)
elif var == 'emp':
    lev = np.arange(-30,32,2)
    plot_EMP(ERA_fluxes,tind,lev)
    if savefig:
        plt.savefig(__figdir__ + site_name + '_EMP_map',**savefig_args)

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
    plt.savefig(movie_dir + site_name + '_map_' + str(tind).zfill(4),**savefig_args)
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
    elif var == 'tcwv': plot_TCWV(ERA_moisture,tind,lev)
    elif var == 'ivt': plot_IVT(ERA_moisture,tind,lev)
    elif var == 'vimdf': plot_VIMDF(ERA_moisture,tind,lev)
    elif var == 'evap': plot_evap_rate(ERA_fluxes,tind,lev)
    elif var == 'emp': plot_EMP(ERA_fluxes,tind,lev)
    # Plot WG positions

    # plt.legend()
    plt.savefig(movie_dir + site_name + '_map_' + str(tind).zfill(4),**savefig_args)
    plt.close()


# parallel version of the above loop
if __name__ == "__main__":
    # This will parallelize a for loop over loop_idx:
    tind = range(0,int(len(time)))
    out = process_map(plot_map_parallel, tind,  max_workers=32, chunksize=20)

# %%
# Use ffmpeg to generate the movie
import subprocess
fps = 18
command = [
    'ffmpeg',
    '-y',
    '-framerate', str(fps),  # Frame rate
    '-pattern_type', 'glob',  # Use glob pattern
    '-i', movie_dir + '*.png',  # Input format with glob pattern for PNG files
    '-vf', "crop=trunc(iw/2)*2:trunc(ih/2)*2",  # Crop to even dimensions
    '-c:v', 'libx264',  # Codec: H.264
    '-pix_fmt', 'yuv420p',  # Pixel format
    '-crf', '17',  # Constant Rate Factor (quality), aiming for high quality
    __figdir__ + site_name + '_' + var + '_out.mp4'
]
subprocess.run(command)

# %%
# Find the minimum msl at each time
min_msl = ERA.msl.min(dim=['latitude','longitude'])/100
# Find max wind speed at each time
max_wind = np.sqrt(ERA.u10**2 + ERA.v10**2).max(dim=['latitude','longitude'])
time_met = ERA.valid_time
fig, axs = plt.subplots(2, 1, sharex=True)
axs[0].plot(time_met,min_msl)
axs[0].title.set_text('Minimum SL pressure')
axs[0].set_ylabel('Pressure (mbar)')
axs[0].grid()

axs[1].plot(time_met,max_wind)
axs[1].plot(time_met,max_wind*0+33,'r--')
axs[1].title.set_text('Maximum wind speed')
axs[1].set_ylabel('Wind speed (m/s)')
axs[1].grid()

fig.autofmt_xdate()

plt.savefig(__figdir__ + site_name + '_min_msl_max_wind',**savefig_args)


# %%
