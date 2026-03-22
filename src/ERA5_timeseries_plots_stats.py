# -*- coding: utf-8 -*-
"""
Make time-series plots and statistics of ERA5 surface conditions at Endurance RCA.

Refactored from earlier ERA5 plotting scripts in this repo.

This version matches the single-location timeseries download written by:
    /home/jtomf/Python/ERA5_plots_2024/src/ERA5_ASTRAL_timeseries_extraction_2025.py

See also:
    /home/jtomf/Python/NORSE2023_processing/src/inspect_NORSE_flux.py
for the relative humidity calculation and the multi-panel time-series plot style.

@author: jtomfarrar
jfarrar@whoi.edu
"""

# %%
import datetime as dt
import glob
import os
from pathlib import Path

# %%
# change to the directory where this script is located
home_dir = os.path.expanduser("~")
os.chdir(home_dir + "/Python/ERA5_plots_2024/src")

import ERA5_extraction_tool
import matplotlib as mplt
import matplotlib.pyplot as plt
import numpy as np
import xarray as xr
from mpl_toolkits.basemap import Basemap


# %%
site_name =  'RAMA_12N'#'SAFARI'

if site_name=="RAMA_12N":
    lon_pt = 88.5  # 88 deg 30.0'E
    lat_pt = 12.0  # 12 deg 00.0'N
    dx = 20
    dy = 15
elif site_name=="Endurance_RCA":
    lon_pt = -130.2  # 130 deg 12.0'W
    lat_pt = 44.98   # 44 deg 58.8'N
    dx = 20
    dy = 15
elif site_name=='SAFARI':
    lon_pt = -161 
    lat_pt = 35
    dx = 60
    dy = 25


savefig = True
plotfiletype = "png"
savefig_args = {"bbox_inches": "tight", "pad_inches": 0.2}

plt.rcParams["figure.figsize"] = (5, 4)
plt.rcParams["figure.dpi"] = 100
plt.rcParams["savefig.dpi"] = 400
%matplotlib ipympl

# %%

input_dir = Path("../data/processed/timeseries")
output_dir = Path("../data/processed/timeseries")
output_dir.mkdir(parents=True, exist_ok=True)
fig_dir = Path("../img")
fig_dir.mkdir(parents=True, exist_ok=True)

site_file = output_dir / f"ERA5_surface_{site_name}_site_timeseries.nc"
climatology_file = output_dir / f"ERA5_surface_{site_name}_site_monthly_climatology.nc"
extreme_wave_file = output_dir / f"ERA5_surface_{site_name}_wave_height_gt10m.txt"


# %%
def find_input_file():
    pattern = str(input_dir / f"ERA5_surface_{site_name}_[0-9][0-9][0-9][0-9]_[0-9][0-9][0-9][0-9].nc")
    files = sorted(glob.glob(pattern))

    if not files:
        raise FileNotFoundError(f"No timeseries files found for pattern: {pattern}")

    return files[-1]


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

    derived["wind_speed"].attrs["units"] = "m s-1"
    derived["air_temperature"].attrs["units"] = "degC"
    derived["dewpoint_temperature"].attrs["units"] = "degC"
    derived["sea_surface_temperature"].attrs["units"] = "degC"
    derived["barometric_pressure"].attrs["units"] = "hPa"
    derived["solar_radiation_downwards"].attrs["units"] = "W m-2"
    # derived["solar_radiation_downwards_7day"].attrs["units"] = "W m-2"
    derived["longwave_radiation_downwards"].attrs["units"] = "W m-2"
    derived["relative_humidity"].attrs["units"] = "%"
    derived["wave_height"].attrs["units"] = "m"
    derived["wave_period"].attrs["units"] = "s"
    derived["wave_direction"].attrs["units"] = "degree true"

    keep_vars = [
        "u10",
        "v10",
        "wind_speed",
        "air_temperature",
        "sea_surface_temperature",
        "skin_temperature",
        "relative_humidity",
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
    ds.attrs["history"] = f"{now.strftime('%Y-%m-%d')} ERA5_timeseries_plots_stats.py"
    ds.load()
    ds.to_netcdf(outfile)


# %%
def plot_locator_map(site_ds):
    map_params = {
        "projection": "cyl",
        "lat_1": lat_pt - 5,
        "lat_2": lat_pt + 5,
        "lat_0": lat_pt,
        "lon_0": lon_pt,
        "llcrnrlat": lat_pt - dy,
        "urcrnrlat": lat_pt + dy,
        "llcrnrlon": lon_pt - dx,
        "urcrnrlon": lon_pt + dx,
        "resolution": "l",
    }

    fig = plt.figure(figsize=(8, 5))
    basemap = Basemap(**map_params)
    basemap.drawcountries()
    basemap.fillcontinents(lake_color="aqua")
    basemap.drawcoastlines()
    basemap.drawparallels(range(-90, 90, 5), labels=[1, 0, 0, 0], color=[0.5, 0.5, 0.5])
    basemap.drawmeridians(range(0, 360, 10), labels=[0, 0, 0, 1], color=[0.5, 0.5, 0.5])

    xpt, ypt = basemap(float(site_ds.longitude.values), float(site_ds.latitude.values))
    basemap.plot(xpt, ypt, marker="D", color="m", markersize=8)
    plt.title(f"{site_name} site")

    if savefig:
        plt.savefig(fig_dir / f"{site_name}_map.{plotfiletype}", **savefig_args)


# %%
def _configure_time_axis(ax, time):
    t0 = np.datetime64(time.values[0], 'D')
    t1 = np.datetime64(time.values[-1], 'D')
    nyears = float((t1 - t0) / np.timedelta64(365, 'D'))

    if nyears > 15:
        ax.xaxis.set_major_locator(mplt.dates.YearLocator(5))
        ax.xaxis.set_major_formatter(mplt.dates.DateFormatter('%Y'))
        ax.xaxis.set_minor_locator(mplt.dates.YearLocator())
        plt.setp(ax.get_xticklabels(), rotation=0, ha='center')
    elif nyears > 5:
        ax.xaxis.set_major_locator(mplt.dates.YearLocator(2))
        ax.xaxis.set_major_formatter(mplt.dates.DateFormatter('%Y'))
        ax.xaxis.set_minor_locator(mplt.dates.YearLocator())
        plt.setp(ax.get_xticklabels(), rotation=0, ha='center')
    elif nyears > 2:
        ax.xaxis.set_major_locator(mplt.dates.YearLocator())
        ax.xaxis.set_major_formatter(mplt.dates.DateFormatter('%Y'))
        ax.xaxis.set_minor_locator(mplt.dates.MonthLocator(interval=3))
        plt.setp(ax.get_xticklabels(), rotation=0, ha='center')
    else:
        ax.xaxis.set_major_locator(mplt.dates.MonthLocator(interval=3))
        ax.xaxis.set_major_formatter(mplt.dates.DateFormatter("%b '%y"))
        ax.xaxis.set_minor_locator(mplt.dates.MonthLocator())
        plt.setp(ax.get_xticklabels(), rotation=30, ha='right')


# %%
def plot_main_summary(site_ds, repeated_climatology_ds=None):
    fig, axs = plt.subplots(5, 1, sharex=True, figsize=(10, 8))
    legendkwargs = {"loc": "best", "fontsize": 7, "frameon": True}
    climatology_style = {"linestyle": "--", "color": "darkred", "linewidth": 1.5, "alpha": 0.9}

    wnd = 0
    at = 1
    wav = 2
    press = 3
    rh = 4

    time = site_ds.valid_time
    climatology_time = None
    if repeated_climatology_ds is not None:
        climatology_time = repeated_climatology_ds.valid_time

    axs[wnd].plot(time, site_ds["wind_speed"], label="wind speed")
    if repeated_climatology_ds is not None:
        axs[wnd].plot(climatology_time, repeated_climatology_ds["wind_speed"], label="wind speed monthly clim.", **climatology_style)
    axs[wnd].legend(**legendkwargs)
    axs[wnd].set(ylabel="[m/s]")
    axs[wnd].title.set_text(f"ERA5 summary at {site_name}")

    axs[at].plot(time, site_ds["air_temperature"], label="air temp")
    axs[at].plot(time, site_ds["sea_surface_temperature"], label="SST")
    if repeated_climatology_ds is not None:
        axs[at].plot(climatology_time, repeated_climatology_ds["air_temperature"], label="air temp monthly clim.", **climatology_style)
        axs[at].plot(climatology_time, repeated_climatology_ds["sea_surface_temperature"], label="SST monthly clim.", **climatology_style)
    #axs[at].plot(time, 0 * site_ds["air_temperature"], "k--")
    axs[at].legend(**legendkwargs)
    axs[at].set(ylabel="[$^\circ$C]")

    axs[wav].plot(time, site_ds["wave_height"], label="wave height")
    if repeated_climatology_ds is not None:
        axs[wav].plot(climatology_time, repeated_climatology_ds["wave_height"], label="wave height monthly clim.", **climatology_style)
    axs[wav].legend(**legendkwargs)
    axs[wav].set(ylabel="[m]")

    axs[press].plot(time, site_ds["barometric_pressure"], label="pressure")
    if repeated_climatology_ds is not None:
        axs[press].plot(climatology_time, repeated_climatology_ds["barometric_pressure"], label="pressure monthly clim.", **climatology_style)
    axs[press].legend(**legendkwargs)
    axs[press].set(ylabel="[hPa]")

    axs[rh].plot(time, site_ds["relative_humidity"], label="RH")
    if repeated_climatology_ds is not None:
        axs[rh].plot(climatology_time, repeated_climatology_ds["relative_humidity"], label="RH monthly clim.", **climatology_style)
    axs[rh].legend(**legendkwargs)
    axs[rh].set(ylabel="[%]")

    for ax in axs:
        _configure_time_axis(ax, site_ds.valid_time)

    plt.tight_layout()
    plt.subplots_adjust(hspace=0.1)

    if savefig:
        plt.savefig(fig_dir / f"{site_name}_main_summary.{plotfiletype}", **savefig_args)


# %%
def plot_supplemental_summary(site_ds, repeated_climatology_ds=None):
    fig, axs = plt.subplots(4, 1, sharex=True, figsize=(10, 8))
    legendkwargs = {"loc": "best", "fontsize": 7, "frameon": True}
    climatology_style = {"linestyle": "--", "color": "darkred", "linewidth": 1.5, "alpha": 0.9}
    time = site_ds.valid_time
    climatology_time = None
    if repeated_climatology_ds is not None:
        climatology_time = repeated_climatology_ds.valid_time

    axs[0].plot(time, site_ds["u10"], label="u10")
    axs[0].plot(time, site_ds["v10"], label="v10")
    if repeated_climatology_ds is not None:
        axs[0].plot(climatology_time, repeated_climatology_ds["u10"], label="u10 monthly clim.", **climatology_style)
        axs[0].plot(climatology_time, repeated_climatology_ds["v10"], label="v10 monthly clim.", **climatology_style)
    axs[0].legend(**legendkwargs)
    axs[0].set(ylabel="[m/s]")
    axs[0].title.set_text("Wind components, radiation, and wave properties")

    axs[1].plot(time, site_ds["solar_radiation_downwards"].rolling(valid_time=24 * 7, center=True, min_periods=1).mean(), label="SW down (7-day avg)")
    axs[1].plot(time, site_ds["longwave_radiation_downwards"], label="LW down")
    if repeated_climatology_ds is not None:
        axs[1].plot(climatology_time, repeated_climatology_ds["solar_radiation_downwards"], label="SW down monthly clim.", **climatology_style)
        axs[1].plot(climatology_time, repeated_climatology_ds["longwave_radiation_downwards"], label="LW down monthly clim.", **climatology_style)
    axs[1].legend(**legendkwargs)
    axs[1].set(ylabel="[W/m$^2$]")

    axs[2].plot(time, site_ds["wave_period"], label="wave period")
    if repeated_climatology_ds is not None:
        axs[2].plot(climatology_time, repeated_climatology_ds["wave_period"], label="wave period monthly clim.", **climatology_style)
    axs[2].legend(**legendkwargs)
    axs[2].set(ylabel="[s]")

    axs[3].plot(time, site_ds["wave_direction"], label="wave direction")
    if repeated_climatology_ds is not None:
        axs[3].plot(climatology_time, repeated_climatology_ds["wave_direction"], label="wave direction monthly clim.", **climatology_style)
    axs[3].legend(**legendkwargs)
    axs[3].set(ylabel="[deg true]")

    for ax in axs:
        _configure_time_axis(ax, site_ds.valid_time)

    plt.tight_layout()
    plt.subplots_adjust(hspace=0.1)

    if savefig:
        plt.savefig(fig_dir / f"{site_name}_supplemental_summary.{plotfiletype}", **savefig_args)


# %%
def add_histogram_stats(ax, values):
    mean_val = float(np.nanmean(values))
    max_val = float(np.nanmax(values))
    p99_val = float(np.nanpercentile(values, 99.9))
    stats_text = f"mean = {mean_val:.2f}\nmax = {max_val:.2f}\n99.9% = {p99_val:.2f}"
    ax.text(
        0.98,
        0.98,
        stats_text,
        ha="right",
        va="top",
        transform=ax.transAxes,
        bbox={"facecolor": "white", "alpha": 0.8, "edgecolor": "0.5"},
    )


# %%
def plot_histograms(site_ds):
    fig, axs = plt.subplots(3, 1, figsize=(7, 9))
    histogram_specs = [
        ("wind_speed", "Wind speed", "[m/s]"),
        ("wave_height", "Wave height", "[m]"),
        ("air_temperature", "Air temperature", "[$^\circ$C]"),
    ]

    for ax, (var_name, title, xlabel) in zip(axs, histogram_specs):
        values = site_ds[var_name].values
        values = values[np.isfinite(values)]
        ax.hist(values, bins=40, color="0.6", edgecolor="k")
        ax.set_title(title)
        ax.set_xlabel(xlabel)
        ax.set_ylabel("Count")
        add_histogram_stats(ax, values)

    plt.tight_layout()
    if savefig:
        plt.savefig(fig_dir / f"{site_name}_histograms.{plotfiletype}", **savefig_args)


# %%
def compute_monthly_climatology(site_ds):
    climatology_ds = site_ds.groupby("valid_time.month").mean()
    climatology_ds.attrs["site_name"] = site_name
    climatology_ds.attrs["site_longitude"] = float(site_ds.longitude.values)
    climatology_ds.attrs["site_latitude"] = float(site_ds.latitude.values)
    return climatology_ds


# %%
def repeat_monthly_climatology(site_ds, climatology_ds):
    year_min = int(site_ds["valid_time"].dt.year.min().item())
    year_max = int(site_ds["valid_time"].dt.year.max().item())
    anchor_years = np.arange(year_min, year_max + 1)
    anchor_time = np.array(
        [np.datetime64(f"{year:04d}-{month:02d}-15") for year in anchor_years for month in range(1, 13)]
    )
    repeated_ds = xr.Dataset(coords={"valid_time": anchor_time})

    for var_name in climatology_ds.data_vars:
        repeated_ds[var_name] = xr.DataArray(
            np.tile(climatology_ds[var_name].values, len(anchor_years)),
            coords={"valid_time": anchor_time},
            dims=("valid_time",),
            attrs=climatology_ds[var_name].attrs,
        )

    repeated_ds.attrs["site_name"] = site_name
    repeated_ds.attrs["site_longitude"] = float(site_ds.longitude.values)
    repeated_ds.attrs["site_latitude"] = float(site_ds.latitude.values)

    if len(repeated_ds.valid_time) >= len(site_ds.valid_time):
        raise ValueError("Monthly climatology overlay is still on the full time axis.")

    return repeated_ds


# %%
def plot_monthly_climatology(climatology_ds):
    fig, axs = plt.subplots(5, 2, figsize=(10, 12), sharex=True)
    month = climatology_ds["month"]
    month_labels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

    plot_specs = [
        ("wind_speed", "Wind speed", "[m/s]"),
        ("u10", "u wind", "[m/s]"),
        ("v10", "v wind", "[m/s]"),
        ("wave_height", "Wave height", "[m]"),
        ("air_temperature", "Air temperature", "[$^\circ$C]"),
        ("sea_surface_temperature", "SST", "[$^\circ$C]"),
        #("skin_temperature", "Skin temperature", "[$^\circ$C]"),
        ("relative_humidity", "Relative humidity", "[%]"),
        ("solar_radiation_downwards", "Solar radiation down", "[W/m$^2$]"),
        ("longwave_radiation_downwards", "Longwave radiation down", "[W/m$^2$]"),
        ("barometric_pressure", "Barometric pressure", "[hPa]"),
    ]

    for ax, (var_name, title, ylabel) in zip(axs.flat, plot_specs):
        ax.plot(month, climatology_ds[var_name], marker="o")
        ax.set_title(title)
        ax.set_ylabel(ylabel)
        ax.grid(True, color="0.85")
        ax.set_xticks(np.arange(1, 13))
        ax.set_xticklabels(month_labels, rotation=45)

    plt.tight_layout()
    if savefig:
        plt.savefig(fig_dir / f"{site_name}_monthly_climatology.{plotfiletype}", **savefig_args)


# %%
def print_summary(raw_file, normalized_file, site_ds):
    print(f"Input timeseries file: {raw_file}")
    print(f"Normalized readable file: {normalized_file}")
    print(f"Saved site time series: {site_file}")
    print(f"Saved monthly climatology: {climatology_file}")
    print(f"Saved extreme wave list: {extreme_wave_file}")
    print(site_ds)


# %%
def save_extreme_wave_events(site_ds, threshold=10.0):
    # Find wave heights greater than the threshold and save the event list.
    event_mask = site_ds["wave_height"] > threshold
    event_ds = site_ds[["wave_height", "wave_period"]].where(event_mask, drop=True)

    with open(extreme_wave_file, "w") as outfile:
        outfile.write(f"{site_name} wave events with wave_height > {threshold:.1f} m\n")
        outfile.write("valid_time,wave_height_m,wave_period_s\n")
        for time_val, wave_height, wave_period in zip(
            event_ds["valid_time"].values,
            event_ds["wave_height"].values,
            event_ds["wave_period"].values,
        ):
            time_str = np.datetime_as_string(time_val, unit="s")
            outfile.write(f"{time_str},{wave_height:.3f},{wave_period:.3f}\n")

    return event_ds


# %%
timeseries_file = find_input_file()

# %%
raw_ds, normalized_file = open_timeseries_file(timeseries_file)

# %%
site_ds = derive_site_variables(raw_ds)

# %%
save_dataset(site_ds, site_file)

# %%
climatology_ds = compute_monthly_climatology(site_ds)

# %%
save_dataset(climatology_ds, climatology_file)

# %%
repeated_climatology_ds = repeat_monthly_climatology(site_ds, climatology_ds)

# %%
plot_locator_map(site_ds)

# %%
plot_main_summary(site_ds, repeated_climatology_ds=repeated_climatology_ds)

# %%
plot_supplemental_summary(site_ds, repeated_climatology_ds=repeated_climatology_ds)

# %%
plot_histograms(site_ds)

# %%
plot_monthly_climatology(climatology_ds)

# %%
extreme_wave_ds = save_extreme_wave_events(site_ds, threshold=10.0)

# %%
print_summary(timeseries_file, normalized_file, site_ds)
