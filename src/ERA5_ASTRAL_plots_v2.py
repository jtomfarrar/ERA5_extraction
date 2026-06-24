# -*- coding: utf-8 -*-
"""
Make ERA5 surface map plots for the ASTRAL 2025 Bay of Bengal campaign.

Generates static maps, animated movies, and min-SLP / max-wind timeseries.
Optionally overlays Wave Glider positions (set plot_WG = True and update WG_data_dir).

Modified from ERA5_ASTRAL_plots_v2.py (ASTRAL 2024) Aug 2024 → May 2025.

@author: jtomfarrar
jfarrar@whoi.edu
"""
# %%
import os
from pathlib import Path
from mpl_toolkits.basemap import Basemap
import numpy as np
import matplotlib.pyplot as plt
import xarray as xr
import glob
from tqdm.contrib.concurrent import process_map
import ERA5_extraction_tool

# %%
home_dir = Path.home()
os.chdir(home_dir / 'Python/ERA5_extraction/src')

# %%
site_name = 'ASTRAL_2025'
lon_pt = 87.6   # approximate ASTRAL 2025 WG cluster centre
lat_pt = 13.2

# %%
__figdir__ = Path('../img/')
__figdir__.mkdir(parents=True, exist_ok=True)
savefig_args = {'bbox_inches': 'tight', 'pad_inches': 0.2}
savefig = True

movie_dir = str(__figdir__ / 'movie_frames') + '/'
if not os.path.exists(movie_dir):
    os.makedirs(movie_dir)

plot_WG = True   # set False if 2025 WG L3 data is not yet available
WG_data_dir = Path('/mnt/d/tom_data/ASTRAL/2025/data/L3/')  # update path / filenames as needed
WG_list = ['Ida', 'Kelvin', 'Planck', 'WHOI43','WHOI1102']
WG_colors = {WG: f'C{i}' for i, WG in enumerate(WG_list)}

plot_ship = True
ship_data_path = Path('/mnt/d/tom_data/ASTRAL/2025/data/ship_data/ASTRAL_2025_gps_compiled.nc')
ship_color = 'C5'
tail_hours = 24

ip = get_ipython() if 'get_ipython' in globals() else None
if ip is not None:
    ip.run_line_magic('matplotlib', 'widget')

plt.rcParams['figure.figsize'] = (5, 4)
plt.rcParams['figure.dpi'] = 100
plt.rcParams['savefig.dpi'] = 400

# %%
# Load ERA5 data.
# _ensure_netcdf_from_cds extracts and merges any ZIP the CDS returned in place of a NetCDF.
path = Path('../data/processed/')
filename      = ERA5_extraction_tool._ensure_netcdf_from_cds(str(path / 'ERA5_surface_ASTRAL_big_2025_2025.nc'))
filename_wave = ERA5_extraction_tool._ensure_netcdf_from_cds(str(path / 'ERA5_surface_ASTRAL_big_2025_waves_2025.nc'))
ERA       = xr.open_dataset(filename)
ERA_waves = xr.open_dataset(filename_wave)

# %%
# Load Wave Glider position data (2025 L3).
# Update WG_data_dir and the filename pattern below to match the actual 2025 WG files.
WG_datasets = {}
if plot_WG:
    for WG in WG_list:
        WG_datasets[WG] = xr.open_dataset(WG_data_dir / f'ASTRAL_2025_waveglider_L3_{WG}_5min_v1.nc', decode_times=True)

# %%
# Load ship GPS data (RV Thomas G. Thompson).
ds_ship = None
if plot_ship:
    ds_ship = xr.open_dataset(ship_data_path, decode_times=True)

# %%
def plot_map(ERA, tind, lev):
    atmp = ERA.t2m[tind, :, :] - 273.15
    U    = ERA.u10[tind, :, :]
    V    = ERA.v10[tind, :, :]
    lon  = ERA.longitude
    lat  = ERA.latitude
    lonmesh, latmesh = np.meshgrid(lon, lat)

    fig = plt.figure(figsize=(8, 5))
    m = Basemap(**cyl_params)
    x, y = m(lonmesh, latmesh)
    m.drawcountries()
    m.fillcontinents(lake_color='aqua')
    C1 = m.contourf(x, y, atmp, cmap='coolwarm', levels=lev)
    sst = ERA.sst[tind, :, :] - 273.15
    m.contour(x, y, sst, levels=lev, colors='k', linewidths=3.0)
    m.contour(x, y, sst, levels=lev, cmap='coolwarm', linewidths=2.5)
    m.drawcoastlines()
    m.drawparallels(range(-90, 90, 5), labels=[1, 0, 0, 0])
    m.drawmeridians(range(0, 360, 10), labels=[0, 0, 0, 1])
    plt.title(time[tind].values)
    m.colorbar(C1, location='right', size='5%', pad='2%', label='Air temp. ($^\circ$C)')
    xpt, ypt = m(lon_pt, lat_pt)
    m.plot(xpt, ypt, marker='D', color='m')
    skipx, skipy = 3, 3
    scale = 300
    q = m.quiver(x[1:-1:skipy, 1:-1:skipx], y[1:-1:skipy, 1:-1:skipx],
                 U[1:-1:skipy, 1:-1:skipx], V[1:-1:skipy, 1:-1:skipx],
                 scale_units='width', scale=scale, color='k')
    plt.quiverkey(q, 0.3, 0.06, 10, '10 m/s', labelpos='E', coordinates='figure')
    time0 = ERA.valid_time[tind].values
    if plot_ship and ds_ship is not None:
        ti = np.argmin(np.abs(ds_ship.dday.values - time0))
        if np.abs(ds_ship.dday.values[ti] - time0) <= np.timedelta64(1, 'h'):
            tail_mask = (ds_ship.dday.values >= time0 - np.timedelta64(tail_hours, 'h')) & \
                        (ds_ship.dday.values <= time0)
            if tail_mask.any():
                xtail, ytail = m(ds_ship.lon.values[tail_mask], ds_ship.lat.values[tail_mask])
                m.plot(xtail, ytail, '-', color=ship_color, alpha=0.4, linewidth=0.8)
            xship, yship = m(float(ds_ship.lon[ti].values), float(ds_ship.lat[ti].values))
            m.plot(xship, yship, '*', color=ship_color, markersize=8, label='Ship (TGT)')
    if plot_WG:
        for WG, ds_wg in WG_datasets.items():
            ti = np.argmin(np.abs(ds_wg.time.values - time0))
            if np.abs(ds_wg.time.values[ti] - time0) <= np.timedelta64(1, 'h'):
                tail_mask = (ds_wg.time.values >= time0 - np.timedelta64(tail_hours, 'h')) & \
                            (ds_wg.time.values <= time0)
                if tail_mask.any():
                    xtail, ytail = m(ds_wg.longitude.values[tail_mask], ds_wg.latitude.values[tail_mask])
                    m.plot(xtail, ytail, '-', color=WG_colors[WG], alpha=0.4, linewidth=0.8)
                xwg, ywg = m(ds_wg.longitude[ti].values, ds_wg.latitude[ti].values)
                m.plot(xwg, ywg, '.', color=WG_colors[WG], label=WG)

# %%
def contour_SLP(ERA, tind, lev):
    U   = ERA.u10[tind, :, :]
    V   = ERA.v10[tind, :, :]
    msl = ERA.msl[tind, :, :] / 100
    lon = ERA.longitude
    lat = ERA.latitude
    lonmesh, latmesh = np.meshgrid(lon, lat)

    fig = plt.figure(figsize=(8, 5))
    m = Basemap(**cyl_params)
    x, y = m(lonmesh, latmesh)
    m.drawcountries()
    m.fillcontinents(lake_color='aqua')
    C1 = m.contourf(x, y, msl, cmap='turbo', levels=lev)
    m.drawcoastlines()
    m.drawparallels(range(-90, 90, 5), labels=[1, 0, 0, 0])
    m.drawmeridians(range(0, 360, 10), labels=[0, 0, 0, 1])
    plt.title(time[tind].values)
    m.colorbar(C1, location='right', size='5%', pad='2%', label='SLP (mb)')
    xpt, ypt = m(lon_pt, lat_pt)
    m.plot(xpt, ypt, marker='D', color='m')
    skipx, skipy = 3, 3
    scale = 300
    q = m.quiver(x[1:-1:skipy, 1:-1:skipx], y[1:-1:skipy, 1:-1:skipx],
                 U[1:-1:skipy, 1:-1:skipx], V[1:-1:skipy, 1:-1:skipx],
                 scale_units='width', scale=scale, color='k')
    plt.quiverkey(q, 0.3, 0.06, 10, '10 m/s', labelpos='E', coordinates='figure')
    time0 = ERA.valid_time[tind].values
    if plot_ship and ds_ship is not None:
        ti = np.argmin(np.abs(ds_ship.dday.values - time0))
        if np.abs(ds_ship.dday.values[ti] - time0) <= np.timedelta64(1, 'h'):
            tail_mask = (ds_ship.dday.values >= time0 - np.timedelta64(tail_hours, 'h')) & \
                        (ds_ship.dday.values <= time0)
            if tail_mask.any():
                xtail, ytail = m(ds_ship.lon.values[tail_mask], ds_ship.lat.values[tail_mask])
                m.plot(xtail, ytail, '-', color=ship_color, alpha=0.4, linewidth=0.8)
            xship, yship = m(float(ds_ship.lon[ti].values), float(ds_ship.lat[ti].values))
            m.plot(xship, yship, '*', color=ship_color, markersize=8, label='Ship (TGT)')
    if plot_WG:
        for WG, ds_wg in WG_datasets.items():
            ti = np.argmin(np.abs(ds_wg.time.values - time0))
            if np.abs(ds_wg.time.values[ti] - time0) <= np.timedelta64(1, 'h'):
                tail_mask = (ds_wg.time.values >= time0 - np.timedelta64(tail_hours, 'h')) & \
                            (ds_wg.time.values <= time0)
                if tail_mask.any():
                    xtail, ytail = m(ds_wg.longitude.values[tail_mask], ds_wg.latitude.values[tail_mask])
                    m.plot(xtail, ytail, '-', color=WG_colors[WG], alpha=0.4, linewidth=0.8)
                xwg, ywg = m(ds_wg.longitude[ti].values, ds_wg.latitude[ti].values)
                m.plot(xwg, ywg, '.', color=WG_colors[WG], label=WG)

# %%
def plot_SST(ERA, tind, lev):
    sst = ERA.sst[tind, :, :] - 273.15
    U   = ERA.u10[tind, :, :]
    V   = ERA.v10[tind, :, :]
    lon = ERA.longitude
    lat = ERA.latitude
    lonmesh, latmesh = np.meshgrid(lon, lat)

    fig = plt.figure(figsize=(8, 5))
    m = Basemap(**cyl_params)
    x, y = m(lonmesh, latmesh)
    m.drawcountries()
    m.fillcontinents(lake_color='aqua')
    C1 = m.contourf(x, y, sst, cmap='coolwarm', levels=lev)
    m.drawcoastlines()
    m.drawparallels(range(-90, 90, 5), labels=[1, 0, 0, 0])
    m.drawmeridians(range(0, 360, 10), labels=[0, 0, 0, 1])
    plt.title(time[tind].values)
    m.colorbar(C1, location='right', size='5%', pad='2%', label='SST ($^\circ$C)')
    skipx, skipy = 3, 3
    scale = 300
    q = m.quiver(x[1:-1:skipy, 1:-1:skipx], y[1:-1:skipy, 1:-1:skipx],
                 U[1:-1:skipy, 1:-1:skipx], V[1:-1:skipy, 1:-1:skipx],
                 scale_units='width', scale=scale, color='k')
    plt.quiverkey(q, 0.3, 0.06, 10, '10 m/s', labelpos='E', coordinates='figure')
    time0 = ERA.valid_time[tind].values
    if plot_ship and ds_ship is not None:
        ti = np.argmin(np.abs(ds_ship.dday.values - time0))
        if np.abs(ds_ship.dday.values[ti] - time0) <= np.timedelta64(1, 'h'):
            tail_mask = (ds_ship.dday.values >= time0 - np.timedelta64(tail_hours, 'h')) & \
                        (ds_ship.dday.values <= time0)
            if tail_mask.any():
                xtail, ytail = m(ds_ship.lon.values[tail_mask], ds_ship.lat.values[tail_mask])
                m.plot(xtail, ytail, '-', color=ship_color, alpha=0.4, linewidth=0.8)
            xship, yship = m(float(ds_ship.lon[ti].values), float(ds_ship.lat[ti].values))
            m.plot(xship, yship, '*', color=ship_color, markersize=8, label='Ship (TGT)')
    if plot_WG:
        for WG, ds_wg in WG_datasets.items():
            ti = np.argmin(np.abs(ds_wg.time.values - time0))
            if np.abs(ds_wg.time.values[ti] - time0) <= np.timedelta64(1, 'h'):
                tail_mask = (ds_wg.time.values >= time0 - np.timedelta64(tail_hours, 'h')) & \
                            (ds_wg.time.values <= time0)
                if tail_mask.any():
                    xtail, ytail = m(ds_wg.longitude.values[tail_mask], ds_wg.latitude.values[tail_mask])
                    m.plot(xtail, ytail, '-', color=WG_colors[WG], alpha=0.4, linewidth=0.8)
                xwg, ywg = m(ds_wg.longitude[ti].values, ds_wg.latitude[ti].values)
                m.plot(xwg, ywg, '.', color=WG_colors[WG], label=WG)

# %%
def plot_SWH(ERA, tind, lev):
    U    = ERA.u10[tind, :, :]
    V    = ERA.v10[tind, :, :]
    lon  = ERA.longitude
    lat  = ERA.latitude
    lonmesh,  latmesh  = np.meshgrid(lon, lat)
    swh  = ERA_waves.swh[tind, :, :]
    lonw = ERA_waves.longitude
    latw = ERA_waves.latitude
    lonmeshw, latmeshw = np.meshgrid(lonw, latw)

    fig = plt.figure(figsize=(8, 5))
    m = Basemap(**cyl_params)
    xw, yw = m(lonmeshw, latmeshw)
    x,  y  = m(lonmesh,  latmesh)
    m.drawcountries()
    m.fillcontinents(lake_color='aqua')
    C1 = m.contourf(xw, yw, swh, cmap='coolwarm', levels=lev)
    m.drawcoastlines()
    m.drawparallels(range(-90, 90, 5), labels=[1, 0, 0, 0])
    m.drawmeridians(range(0, 360, 10), labels=[0, 0, 0, 1])
    plt.title(time[tind].values)
    m.colorbar(C1, location='right', size='5%', pad='2%', label='SWH (m)')
    skipx, skipy = 3, 3
    scale = 300
    q = m.quiver(x[1:-1:skipy, 1:-1:skipx], y[1:-1:skipy, 1:-1:skipx],
                 U[1:-1:skipy, 1:-1:skipx], V[1:-1:skipy, 1:-1:skipx],
                 scale_units='width', scale=scale, color='k')
    plt.quiverkey(q, 0.3, 0.06, 10, '10 m/s', labelpos='E', coordinates='figure')
    time0 = ERA.valid_time[tind].values
    if plot_ship and ds_ship is not None:
        ti = np.argmin(np.abs(ds_ship.dday.values - time0))
        if np.abs(ds_ship.dday.values[ti] - time0) <= np.timedelta64(1, 'h'):
            tail_mask = (ds_ship.dday.values >= time0 - np.timedelta64(tail_hours, 'h')) & \
                        (ds_ship.dday.values <= time0)
            if tail_mask.any():
                xtail, ytail = m(ds_ship.lon.values[tail_mask], ds_ship.lat.values[tail_mask])
                m.plot(xtail, ytail, '-', color=ship_color, alpha=0.4, linewidth=0.8)
            xship, yship = m(float(ds_ship.lon[ti].values), float(ds_ship.lat[ti].values))
            m.plot(xship, yship, '*', color=ship_color, markersize=8, label='Ship (TGT)')
    if plot_WG:
        for WG, ds_wg in WG_datasets.items():
            ti = np.argmin(np.abs(ds_wg.time.values - time0))
            if np.abs(ds_wg.time.values[ti] - time0) <= np.timedelta64(1, 'h'):
                tail_mask = (ds_wg.time.values >= time0 - np.timedelta64(tail_hours, 'h')) & \
                            (ds_wg.time.values <= time0)
                if tail_mask.any():
                    xtail, ytail = m(ds_wg.longitude.values[tail_mask], ds_wg.latitude.values[tail_mask])
                    m.plot(xtail, ytail, '-', color=WG_colors[WG], alpha=0.4, linewidth=0.8)
                xwg, ywg = m(ds_wg.longitude[ti].values, ds_wg.latitude[ti].values)
                m.plot(xwg, ywg, '.', color=WG_colors[WG], label=WG)

# %%
def _add_position_overlays(m, time0):
    xpt, ypt = m(lon_pt, lat_pt)
    m.plot(xpt, ypt, marker='D', color='m')
    if plot_ship and ds_ship is not None:
        ti = np.argmin(np.abs(ds_ship.dday.values - time0))
        if np.abs(ds_ship.dday.values[ti] - time0) <= np.timedelta64(1, 'h'):
            tail_mask = (ds_ship.dday.values >= time0 - np.timedelta64(tail_hours, 'h')) & \
                        (ds_ship.dday.values <= time0)
            if tail_mask.any():
                xtail, ytail = m(ds_ship.lon.values[tail_mask], ds_ship.lat.values[tail_mask])
                m.plot(xtail, ytail, '-', color=ship_color, alpha=0.4, linewidth=0.8)
            xship, yship = m(float(ds_ship.lon[ti].values), float(ds_ship.lat[ti].values))
            m.plot(xship, yship, '*', color=ship_color, markersize=8, label='Ship (TGT)')
    if plot_WG:
        for WG, ds_wg in WG_datasets.items():
            ti = np.argmin(np.abs(ds_wg.time.values - time0))
            if np.abs(ds_wg.time.values[ti] - time0) <= np.timedelta64(1, 'h'):
                tail_mask = (ds_wg.time.values >= time0 - np.timedelta64(tail_hours, 'h')) & \
                            (ds_wg.time.values <= time0)
                if tail_mask.any():
                    xtail, ytail = m(ds_wg.longitude.values[tail_mask], ds_wg.latitude.values[tail_mask])
                    m.plot(xtail, ytail, '-', color=WG_colors[WG], alpha=0.4, linewidth=0.8)
                xwg, ywg = m(ds_wg.longitude[ti].values, ds_wg.latitude[ti].values)
                m.plot(xwg, ywg, '.', color=WG_colors[WG], label=WG)


def _draw_atmp_sst_panel(fig, ax, lonmesh, latmesh, field, U, V, levels, title, cbar_label, time0):
    m = Basemap(ax=ax, **cyl_params)
    x, y = m(lonmesh, latmesh)
    m.drawcountries()
    m.fillcontinents(lake_color='aqua')
    C1 = m.contourf(x, y, field, cmap='coolwarm', levels=levels)
    m.drawcoastlines()
    m.drawparallels(range(-90, 90, 5), labels=[1, 0, 0, 0])
    m.drawmeridians(range(0, 360, 10), labels=[0, 0, 0, 1])
    ax.set_title(title)
    fig.colorbar(C1, ax=ax, shrink=0.82, pad=0.02, label=cbar_label)
    skipx, skipy = 3, 3
    scale = 300
    q = m.quiver(x[1:-1:skipy, 1:-1:skipx], y[1:-1:skipy, 1:-1:skipx],
                 U[1:-1:skipy, 1:-1:skipx], V[1:-1:skipy, 1:-1:skipx],
                 scale_units='width', scale=scale, color='k')
    ax.quiverkey(q, 0.12, -0.08, 10, '10 m/s', labelpos='E', coordinates='axes')
    _add_position_overlays(m, time0)


def plot_ATMP_SST(ERA, tind, atmp_lev, sst_lev):
    atmp = ERA.t2m[tind, :, :] - 273.15
    sst  = ERA.sst[tind, :, :] - 273.15
    U    = ERA.u10[tind, :, :]
    V    = ERA.v10[tind, :, :]
    lon  = ERA.longitude
    lat  = ERA.latitude
    lonmesh, latmesh = np.meshgrid(lon, lat)
    time0 = ERA.valid_time[tind].values

    fig, axs = plt.subplots(1, 2, figsize=(14, 5), constrained_layout=True)
    _draw_atmp_sst_panel(fig, axs[0], lonmesh, latmesh, atmp, U, V, atmp_lev,
                         'Air temperature', 'Air temp. ($^\circ$C)', time0)
    _draw_atmp_sst_panel(fig, axs[1], lonmesh, latmesh, sst, U, V, sst_lev,
                         'SST', 'SST ($^\circ$C)', time0)
    fig.suptitle(time[tind].values)

# %%
time = ERA.valid_time

dx = 15   # lon_pt=85 ± 15  →  70–100°E
dy = 10   # lat_pt=11 ± 10  →   1–21°N
cyl_params = {
    'projection': 'cyl',
    'lat_0': lat_pt, 'lon_0': 85,
    'llcrnrlat': lat_pt - dy, 'urcrnrlat': lat_pt + dy,
    'llcrnrlon': 70,           'urcrnrlon': 100,
    'resolution': 'h',
}

# %%
tind = np.where(time == np.datetime64('2025-05-15T12:00:00'))[0][0]

# %%
var = 'atmp_sst'  # 'atmp' | 'slp' | 'sst' | 'swh' | 'atmp_sst'
if var == 'atmp':
    lev = np.arange(17, 36, 1)
    plot_map(ERA, tind, lev)
    if savefig:
        plt.savefig(__figdir__ / 'ASTRAL_2025_ATMP_map', **savefig_args)
elif var == 'slp':
    lev = np.arange(975, 1012, 2)
    contour_SLP(ERA, tind, lev)
    if savefig:
        plt.savefig(__figdir__ / 'ASTRAL_2025_SLP_map', **savefig_args)
elif var == 'sst':
    lev = np.arange(27, 33, .5)
    plot_SST(ERA, tind, lev)
    if savefig:
        plt.savefig(__figdir__ / 'ASTRAL_2025_SST_map', **savefig_args)
elif var == 'swh':
    lev = np.arange(-.1, 5, .1)
    plot_SWH(ERA, tind, lev)
    if savefig:
        plt.savefig(__figdir__ / 'ASTRAL_2025_SWH_map', **savefig_args)
elif var == 'atmp_sst':
    atmp_lev = np.arange(17, 36, 1)
    sst_lev = np.arange(27, 33, .5)
    plot_ATMP_SST(ERA, tind, atmp_lev, sst_lev)
    if savefig:
        plt.savefig(__figdir__ / 'ASTRAL_2025_ATMP_SST_map', **savefig_args)

# %%
# Clear movie_frames directory and regenerate frames in parallel
files = glob.glob(movie_dir + '*')
for f in files:
    os.remove(f)

# %%
def plot_map_parallel(tind):
    plt.clf()
    if var == 'atmp':
        plot_map(ERA, tind, lev)
    elif var == 'slp':
        contour_SLP(ERA, tind, lev)
    elif var == 'sst':
        plot_SST(ERA, tind, lev)
    elif var == 'swh':
        plot_SWH(ERA, tind, lev)
    elif var == 'atmp_sst':
        plot_ATMP_SST(ERA, tind, atmp_lev, sst_lev)
    for ax in reversed(plt.gcf().axes):
        handles, labels = ax.get_legend_handles_labels()
        if labels:
            ax.legend()
            break
    plt.savefig(movie_dir + 'ASTRAL_2025_map_' + str(tind).zfill(4), **savefig_args)
    plt.close()


if __name__ == '__main__':
    tind_range = range(len(time))
    out = process_map(plot_map_parallel, tind_range)

# %%
import subprocess
fps = 18
command = [
    'ffmpeg',
    '-y',
    '-framerate', str(fps),
    '-pattern_type', 'glob',
    '-i', '../img/movie_frames/*.png',
    '-vf', 'crop=trunc(iw/2)*2:trunc(ih/2)*2',
    '-c:v', 'libx264',
    '-pix_fmt', 'yuv420p',
    '-crf', '17',
    f'../img/ASTRAL_2025_{var}_out.mp4',
]
subprocess.run(command)


# %%
