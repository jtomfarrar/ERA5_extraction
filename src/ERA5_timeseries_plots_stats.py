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




site_name = "Endurance_RCA"
lon_pt = -130.2  # 130 deg 12.0'W
lat_pt = 44.98   # 44 deg 58.8'N

savefig = True
plotfiletype = "png"
savefig_args = {"bbox_inches": "tight", "pad_inches": 0.2}

plt.rcParams["figure.figsize"] = (5, 4)
plt.rcParams["figure.dpi"] = 100
plt.rcParams["savefig.dpi"] = 400

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
    derived["solar_radiation_downwards_7day"].attrs["units"] = "W m-2"
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
        "relative_humidity",
        "solar_radiation_downwards_7day",
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
        "llcrnrlat": 30,
        "urcrnrlat": 55,
        "llcrnrlon": -150,
        "urcrnrlon": -115,
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
    plt.title(f"{site_name} locator map")

    if savefig:
        plt.savefig(fig_dir / f"{site_name}_locator_map.{plotfiletype}", **savefig_args)


# %%
def plot_main_summary(site_ds):
    fig, axs = plt.subplots(5, 1, sharex=True, figsize=(10, 8))
    legendkwargs = {"loc": "best", "fontsize": 7, "frameon": True}

    wnd = 0
    at = 1
    wav = 2
    press = 3
    rh = 4

    time = site_ds.valid_time

    axs[wnd].plot(time, site_ds["wind_speed"], label="wind speed")
    axs[wnd].legend(**legendkwargs)
    axs[wnd].set(ylabel="[m/s]")
    axs[wnd].title.set_text(f"ERA5 summary at {site_name}")

    axs[at].plot(time, site_ds["air_temperature"], label="air temp")
    axs[at].plot(time, site_ds["sea_surface_temperature"], label="SST")
    axs[at].plot(time, 0 * site_ds["air_temperature"], "k--")
    axs[at].legend(**legendkwargs)
    axs[at].set(ylabel="[$^\circ$C]")

    axs[wav].plot(time, site_ds["wave_height"], label="wave height")
    axs[wav].legend(**legendkwargs)
    axs[wav].set(ylabel="[m]")

    axs[press].plot(time, site_ds["barometric_pressure"], label="pressure")
    axs[press].legend(**legendkwargs)
    axs[press].set(ylabel="[hPa]")

    axs[rh].plot(time, site_ds["relative_humidity"], label="RH")
    axs[rh].legend(**legendkwargs)
    axs[rh].set(ylabel="[%]")

    for ax in axs:
        ax.xaxis.set_major_locator(mplt.dates.MonthLocator(interval=6))
        ax.xaxis.set_minor_locator(mplt.dates.MonthLocator())

    plt.tight_layout()
    plt.subplots_adjust(hspace=0.1)
    fig.autofmt_xdate()

    if savefig:
        plt.savefig(fig_dir / f"{site_name}_main_summary.{plotfiletype}", **savefig_args)


# %%
def plot_supplemental_summary(site_ds):
    fig, axs = plt.subplots(4, 1, sharex=True, figsize=(10, 8))
    legendkwargs = {"loc": "best", "fontsize": 7, "frameon": True}
    time = site_ds.valid_time

    axs[0].plot(time, site_ds["u10"], label="u10")
    axs[0].plot(time, site_ds["v10"], label="v10")
    axs[0].legend(**legendkwargs)
    axs[0].set(ylabel="[m/s]")
    axs[0].title.set_text("Wind components, radiation, and wave properties")

    axs[1].plot(time, site_ds["solar_radiation_downwards_7day"], label="SW down (7-day avg)")
    axs[1].plot(time, site_ds["longwave_radiation_downwards"], label="LW down")
    axs[1].legend(**legendkwargs)
    axs[1].set(ylabel="[W/m$^2$]")

    axs[2].plot(time, site_ds["wave_period"], label="wave period")
    axs[2].legend(**legendkwargs)
    axs[2].set(ylabel="[s]")

    axs[3].plot(time, site_ds["wave_direction"], label="wave direction")
    axs[3].legend(**legendkwargs)
    axs[3].set(ylabel="[deg true]")

    for ax in axs:
        ax.xaxis.set_major_locator(mplt.dates.MonthLocator(interval=6))
        ax.xaxis.set_minor_locator(mplt.dates.MonthLocator())

    plt.tight_layout()
    plt.subplots_adjust(hspace=0.1)
    fig.autofmt_xdate()

    if savefig:
        plt.savefig(fig_dir / f"{site_name}_supplemental_summary.{plotfiletype}", **savefig_args)


# %%
def add_histogram_stats(ax, values):
    mean_val = float(np.nanmean(values))
    max_val = float(np.nanmax(values))
    p99_val = float(np.nanpercentile(values, 99))
    stats_text = f"mean = {mean_val:.2f}\nmax = {max_val:.2f}\n99% = {p99_val:.2f}"
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
        ("relative_humidity", "Relative humidity", "[%]"),
        ("solar_radiation_downwards_7day", "Solar radiation down", "[W/m$^2$]"),
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
plot_locator_map(site_ds)

# %%
plot_main_summary(site_ds)

# %%
plot_supplemental_summary(site_ds)

# %%
plot_histograms(site_ds)

# %%
plot_monthly_climatology(climatology_ds)

# %%
extreme_wave_ds = save_extreme_wave_events(site_ds, threshold=10.0)

# %%
print_summary(timeseries_file, normalized_file, site_ds)
