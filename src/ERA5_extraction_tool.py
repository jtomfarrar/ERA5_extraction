# -*- coding: utf-8 -*-
"""

Attempt to read ERA 5 data from https://cds.climate.copernicus.eu/user
https://cds.climate.copernicus.eu/api-how-to

The dataset and API code are here:
    https://cds.climate.copernicus.eu/datasets/reanalysis-era5-single-levels?tab=download

Queued requests can be viewed here:
    https://cds.climate.copernicus.eu/live/queue

In Sept 2024 they updated the CDS API; it mostly works the same as before, except that 
the wave data must be requested separately from other data.
Instructions for the new API are here:
    https://cds-beta.climate.copernicus.eu/how-to-api#install-the-cds-api-token

Created on Wed Jan  6 18:02:24 2021
Updated Sept 1 2024
Extensively refactored June 2024

@author: jtomf
"""
import cdsapi
import datetime
import glob
import os
import shutil
import sys
import time
import zipfile
from pathlib import Path
import xarray as xr
import numpy as np

# N, W, S, E valid range is 90, -180, -90, 180
# could use lon0=0 lat0=0 dlon=180 dlat=90

# E-W valid range is -180, 180
#lon0 = -158 # NORSE=3, WHOTS=-158
#lat0 = 22.67 # NORSE=70, WHOTS=22.67
#dlat = 5
#dlon = 5
#yr = '2011'

ERA5_SINGLE_LEVELS_DATASET = 'reanalysis-era5-single-levels'

ALL_DAYS = [
    '01', '02', '03', '04', '05', '06', '07', '08', '09', '10',
    '11', '12', '13', '14', '15', '16', '17', '18', '19', '20',
    '21', '22', '23', '24', '25', '26', '27', '28', '29', '30', '31',
]

ALL_HOURS = [
    '00:00', '01:00', '02:00', '03:00', '04:00', '05:00',
    '06:00', '07:00', '08:00', '09:00', '10:00', '11:00',
    '12:00', '13:00', '14:00', '15:00', '16:00', '17:00',
    '18:00', '19:00', '20:00', '21:00', '22:00', '23:00',
]

VARIABLE_GROUPS = {
    'surface': [
        '10m_u_component_of_wind',
        '10m_v_component_of_wind',
        '2m_dewpoint_temperature',
        'skin_temperature',
        '2m_temperature',
        'mean_sea_level_pressure',
        'sea_surface_temperature',
        'surface_net_solar_radiation',
        'surface_net_thermal_radiation',
        'surface_pressure',
        'surface_solar_radiation_downwards',
        'surface_thermal_radiation_downwards',
        'total_precipitation',
    ],
    'waves': [
        'peak_wave_period',
        'significant_height_of_combined_wind_waves_and_swell',
        'mean_wave_direction',
    ],
    'moisture': [
        'mean_sea_level_pressure',
        'surface_pressure',
        'vertical_integral_of_divergence_of_moisture_flux',
        'vertical_integral_of_eastward_water_vapour_flux',
        'vertical_integral_of_northward_water_vapour_flux',
        'total_column_water',
        'total_column_water_vapour',
    ],
}


def build_area(lon0, lat0, dlon, dlat):
    '''
    Build a CDS API area list from center point and half-widths.

    Parameters
    ----------
    lon0 : numeric
        Center longitude.
    lat0 : numeric
        Center latitude.
    dlon : numeric
        +/- longitude range around lon0.
    dlat : numeric
        +/- latitude range around lat0.

    Returns
    -------
    list
        Area in CDS order: [north, west, south, east].
    '''
    return [lat0+dlat, lon0-dlon, lat0-dlat, lon0+dlon]


def write_request_readme(output_file, function_name):
    '''
    Write a README when and how an output file was created.

    Parameters
    ----------
    output_file : str or Path
        Path to the NetCDF output file.
    function_name : str
        Name of the function used to write the output file.

    Returns
    -------
    None, but saves a text file next to output_file.
    '''
    output_file = str(output_file)
    calling_fname = str(sys.argv[0])
    output_file_prefix = output_file[:-3]
    ReadmeFile = open(output_file_prefix+"_README.txt", "w")
    ReadmeFile.write ('Written using ERA5_extraction_tool.' + function_name + '() on \n' + str(datetime.datetime.now()) +
                      '\n Invoked from ' + calling_fname)
    ReadmeFile.close()


def get_timeseries(lon0, lat0, startdate, enddate, output_file=None):
    '''
    Extract ERA5 timeseries data using Copernicus Climate Data System API.  
    Given a geographic location and a date range, saves file 'outfile.nc' in local directory

    https://cds.climate.copernicus.eu/datasets/reanalysis-era5-single-levels-timeseries?tab=overview

    Parameters
    ----------
    lon0 : numeric
        Target longitude.
    lat0 : numeric
        Target latitude.
    startdate : str
        Start date in format 'YYYY-MM-DD'.
    enddate : str
        End date in format 'YYYY-MM-DD'.
    output_file (optional) : str
        If provided, output filename is used. Otherwise, 'outfile.nc' is used.

    Returns
    -------
    None, but saves output file in local directory.
    '''
    if output_file is None:
        output_file = 'outfile.nc'
    
    dataset = "reanalysis-era5-single-levels-timeseries"
    request = {
        "variable": [
            "2m_dewpoint_temperature",
            "skin_temperature",
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
        "location": {"longitude": lon0, "latitude": lat0},
        "date": [f"{startdate}/{enddate}"],
        "data_format": "netcdf",
        "download_format": "unarchived",
        "file_name": output_file
    }

    client = cdsapi.Client()
    client.retrieve(dataset, request).download(output_file)

    final_path = _ensure_netcdf_from_cds(output_file)
    print(f"Timeseries data saved at: {final_path}")

    # Write a readme file to say when and by what script the file was written
    calling_fname = str(sys.argv[0])
    output_file_prefix = output_file[:-3]
    ReadmeFile = open(output_file_prefix + "_README.txt", "w")
    ReadmeFile.write(
        'Written using ERA5_extraction_tool.get_timeseries() on \n'
        + str(datetime.datetime.now())
        + '\n Invoked from '
        + calling_fname
    )
    ReadmeFile.close()


def extract_vars_single_month(lon0, lat0, dlon, dlat, yr, mm, variable_group, output_file=None):
    '''
    Extract one month of ERA5 single-level map data for a named variable group.

    Parameters
    ----------
    lon0 : numeric
        Target longitude.
    lat0 : numeric
        Target latitude.
    dlon : numeric
        +/- longitude range around lon0.
    dlat : numeric
        +/- latitude range around lat0.
    yr : str
        Year to extract.
    mm : list of str
        Month or months to extract. Monthly workflows should pass one month,
        e.g. ['10'].
    variable_group : str
        Key in VARIABLE_GROUPS. Current options are 'surface', 'waves',
        and 'moisture'.
    output_file (optional) : str or Path
        If provided, output filename is used. Otherwise, 'outfile.nc' is used.

    Returns
    -------
    str
        Path to a readable NetCDF file saved in local directory.
    '''
    if output_file is None:
        output_file = 'outfile.nc'
    output_file = str(output_file)

    if variable_group not in VARIABLE_GROUPS:
        valid_groups = ', '.join(VARIABLE_GROUPS.keys())
        raise ValueError(f"Unknown variable_group '{variable_group}'. Choose one of: {valid_groups}.")

    c = cdsapi.Client()
    c.retrieve(
        ERA5_SINGLE_LEVELS_DATASET, # DOI: 10.24381/cds.adbb2d47
        {
            'product_type': 'reanalysis',
            'variable': VARIABLE_GROUPS[variable_group],
            'year': yr,
            'month': mm,
            'day': ALL_DAYS,
            'time': ALL_HOURS,
            # area is N, W, S, E; valid range is 90, -180, -90, 180
            'area': build_area(lon0, lat0, dlon, dlat),
            'format': 'netcdf',
            'download_format': 'unarchived',
        },
        output_file)

    final_path = _ensure_netcdf_from_cds(output_file)
    print(f"{variable_group.capitalize()} data saved at: {final_path}")
    write_request_readme(output_file, 'extract_vars_single_month')
    return final_path


def get_surface_vars(lon0, lat0, dlon, dlat, yr, mm, output_file=None):
    '''
    Extract ERA5 surface data using Copernicus Climate Data System API.

    Parameters
    ----------
    lon0 : numeric
        Target longitude.
    lat0 : numeric
        Target latitude.
    dlon : numeric
        +/- longitude range around lon0.
    dlat : numeric
        +/- latitude range around lat0.
    yr : str
        Year to extract.
    mm : list of str
        Month or months to extract.
    output_file (optional) : str or Path
        If provided, output filename is used. Otherwise, 'outfile.nc' is used.

    Returns
    -------
    str
        Path to a readable NetCDF file saved in local directory.
    '''
    return extract_vars_single_month(lon0, lat0, dlon, dlat, yr, mm, 'surface', output_file)


def get_moisture_vars(lon0, lat0, dlon, dlat, yr, mm, output_file=None):
    '''
    Extract ERA5 moisture and column water data using Copernicus Climate Data System API.

    Parameters
    ----------
    lon0 : numeric
        Target longitude.
    lat0 : numeric
        Target latitude.
    dlon : numeric
        +/- longitude range around lon0.
    dlat : numeric
        +/- latitude range around lat0.
    yr : str
        Year to extract.
    mm : list of str
        Month or months to extract.
    output_file (optional) : str or Path
        If provided, output filename is used. Otherwise, 'outfile.nc' is used.

    Returns
    -------
    str
        Path to a readable NetCDF file saved in local directory.
    '''
    return extract_vars_single_month(lon0, lat0, dlon, dlat, yr, mm, 'moisture', output_file)


def get_wave_vars(lon0, lat0, dlon, dlat, yr, mm, output_file=None):
    '''
    Extract ERA5 surface wave data using Copernicus Climate Data System API.

    Parameters
    ----------
    lon0 : numeric
        Target longitude.
    lat0 : numeric
        Target latitude.
    dlon : numeric
        +/- longitude range around lon0.
    dlat : numeric
        +/- latitude range around lat0.
    yr : str
        Year to extract.
    mm : list of str
        Month or months to extract.
    output_file (optional) : str or Path
        If provided, output filename is used. Otherwise, 'outfile.nc' is used.

    Returns
    -------
    str
        Path to a readable NetCDF file saved in local directory.
    '''
    return extract_vars_single_month(lon0, lat0, dlon, dlat, yr, mm, 'waves', output_file)


def iter_year_months(start_year, start_month, end_year, end_month):
    '''
    Return inclusive (year, month) pairs for a month-based date range.

    Parameters
    ----------
    start_year : int
        First year to extract.
    start_month : int
        First month to extract.
    end_year : int
        Last year to extract.
    end_month : int
        Last month to extract.

    Returns
    -------
    generator
        Inclusive sequence of (year, month) pairs.
    '''
    for month in [start_month, end_month]:
        if month < 1 or month > 12:
            raise ValueError("Months must be between 1 and 12.")

    start_index = start_year * 12 + start_month
    end_index = end_year * 12 + end_month
    if start_index > end_index:
        raise ValueError("Start month must be before or equal to end month.")

    for month_index in range(start_index, end_index + 1):
        year, zero_based_month = divmod(month_index - 1, 12)
        yield year, zero_based_month + 1


def date_range_label(start_year, start_month, end_year, end_month):
    '''
    Build a compact label for a month-based date range.

    Parameters
    ----------
    start_year : int
        First year to extract.
    start_month : int
        First month to extract.
    end_year : int
        Last year to extract.
    end_month : int
        Last month to extract.

    Returns
    -------
    str
        Date label in YYYYMM_YYYYMM format.
    '''
    return f"{start_year:04d}{start_month:02d}_{end_year:04d}{end_month:02d}"


def merge_monthly_files(monthly_files, output_file):
    '''
    Merge monthly ERA5 NetCDF files into one compressed NetCDF file.

    Parameters
    ----------
    monthly_files : list of str or Path
        Monthly NetCDF files to merge.
    output_file : str or Path
        Final merged NetCDF file.

    Returns
    -------
    Path
        Path to the merged NetCDF file.
    '''
    output_file = Path(output_file)
    monthly_files = [Path(f) for f in monthly_files]

    print(f"Merging {len(monthly_files)} monthly files -> {output_file}")
    ds = xr.open_mfdataset([str(f) for f in monthly_files], combine='by_coords', engine='h5netcdf')

    for var in list(ds.data_vars) + list(ds.coords):
        ds[var].encoding.clear()

    encoding = {}
    for var in list(ds.data_vars) + list(ds.coords):
        enc = {'zlib': True, 'complevel': 4}
        if np.issubdtype(ds[var].dtype, np.floating):
            enc['dtype'] = 'float32'
            enc['_FillValue'] = np.nan
        encoding[var] = enc

    ds.to_netcdf(output_file, encoding=encoding, engine='h5netcdf')
    ds.close()
    print('Done.')
    return output_file


def extract_monthly_range(lon0, lat0, dlon, dlat, start_year, start_month, end_year, end_month,
                          variable_group, output_file, tmp_dir, monthly_file_prefix=None,
                          sleep_seconds=5, cleanup_tmp=True):
    '''
    Extract ERA5 map data one month at a time and merge the monthly files.

    Parameters
    ----------
    lon0 : numeric
        Target longitude.
    lat0 : numeric
        Target latitude.
    dlon : numeric
        +/- longitude range around lon0.
    dlat : numeric
        +/- latitude range around lat0.
    start_year : int
        First year to extract.
    start_month : int
        First month to extract.
    end_year : int
        Last year to extract.
    end_month : int
        Last month to extract.
    variable_group : str
        Key in VARIABLE_GROUPS. Current options are 'surface', 'waves',
        and 'moisture'.
    output_file : str or Path
        Final merged NetCDF file.
    tmp_dir : str or Path
        Directory for monthly temporary files.
    monthly_file_prefix (optional) : str
        Prefix for monthly NetCDF files. If not provided, output_file.stem is used.
    sleep_seconds (optional) : numeric
        Seconds to wait after each CDS download request.
    cleanup_tmp (optional) : bool
        If True, remove tmp_dir after the merged file is written.

    Returns
    -------
    Path
        Path to the merged NetCDF file.
    '''
    if variable_group not in VARIABLE_GROUPS:
        valid_groups = ', '.join(VARIABLE_GROUPS.keys())
        raise ValueError(f"Unknown variable_group '{variable_group}'. Choose one of: {valid_groups}.")

    output_file = Path(output_file)
    tmp_dir = Path(tmp_dir)
    tmp_dir.mkdir(parents=True, exist_ok=True)

    if monthly_file_prefix is None:
        monthly_file_prefix = output_file.stem

    date_label = date_range_label(start_year, start_month, end_year, end_month)
    monthly_files = []
    year_months = list(iter_year_months(start_year, start_month, end_year, end_month))

    print(f"\nDownloading {variable_group}: {date_label}")
    print('View queue: https://cds.climate.copernicus.eu/requests')

    for year, month in year_months:
        monthly_file = tmp_dir / f"{monthly_file_prefix}_{year:04d}_{month:02d}.nc"
        if monthly_file.exists():
            print(f"  {year:04d}-{month:02d}: already exists, skipping")
        else:
            print(f"  {year:04d}-{month:02d}: downloading ...")
            tic()
            extract_vars_single_month(
                lon0, lat0, dlon, dlat,
                str(year), [f"{month:02d}"], variable_group, monthly_file,
            )
            toc()
            time.sleep(sleep_seconds)
        monthly_files.append(monthly_file)

    merged_file = merge_monthly_files(monthly_files, output_file)
    write_request_readme(merged_file, 'extract_monthly_range')

    if cleanup_tmp:
        shutil.rmtree(tmp_dir)

    return merged_file

'''
Contact

copernicus-support@ecmwf.int
Licence

Licence to use Copernicus Products
Publication date
2018-06-14
References

Citation

DOI: 10.24381/cds.adbb2d47
Related data
ERA5 hourly data on pressure levels from 1950 to 1978 (preliminary version)
ERA5 hourly data on pressure levels from 1979 to present
ERA5 hourly data on single levels from 1950 to 1978 (preliminary version)
ERA5 monthly averaged data on pressure levels from 1950 to 1978 (preliminary version)
ERA5 monthly averaged data on pressure levels from 1979 to present
ERA5 monthly averaged data on single levels from 1950 to 1978 (preliminary version)
ERA5 monthly averaged data on single levels from 1979 to present
'''

'''Clone of matlab tic/toc from Stackoverflow user Benben:
    https://stackoverflow.com/questions/5849800/what-is-the-python-equivalent-of-matlabs-tic-and-toc-functions
'''
def TicTocGenerator():
    # Generator that returns time differences
    ti = 0           # initial time
    tf = time.time() # final time
    while True:
        ti = tf
        tf = time.time()
        yield tf-ti # returns the time difference

TicToc = TicTocGenerator() # create an instance of the TicTocGen generator

# This will be the main function through which we define both tic() and toc()
def toc(tempBool=True):
    # Prints the time difference yielded by generator instance TicToc
    tempTimeInterval = next(TicToc)
    if tempBool:
        print( "Elapsed time: %f seconds.\n" %tempTimeInterval )

def tic():
    # Records a time in TicToc, marks the beginning of a time interval
    toc(False)


def _ensure_netcdf_from_cds(output_path: str, cleanup: bool = True) -> str:
    """
    If CDS returned a ZIP (often happens when variables have different time bases),
    unpack it and merge the contained NetCDF files into a single *_merged.nc.
    Returns the path to a readable NetCDF file.
    """
    # If it's already a valid NetCDF file, leave it
    if not zipfile.is_zipfile(output_path):
        return output_path

    # Rename to .zip (for clarity) and extract
    zip_path = output_path if output_path.endswith('.zip') else output_path + '.zip'
    if zip_path != output_path:
        os.replace(output_path, zip_path)

    extract_dir = os.path.splitext(zip_path)[0] + "_parts"
    os.makedirs(extract_dir, exist_ok=True)
    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall(extract_dir)

    nc_files = sorted(glob.glob(os.path.join(extract_dir, "*.nc")))
    if not nc_files:
        raise RuntimeError(f"No NetCDF files found inside {zip_path}")

    # Try a simple multi-file open, then fall back to manual merge with coord renames
    try:
        ds = xr.open_mfdataset(nc_files, combine="by_coords")
    except Exception:
        ds_list = []
        for f in nc_files:
            d = xr.open_dataset(f)
            # Harmonize coord names if needed
            rename_map = {}
            if "time" in d.dims and "valid_time" not in d.dims:
                rename_map["time"] = "valid_time"
            if "lat" in d.dims and "latitude" not in d.dims:
                rename_map["lat"] = "latitude"
            if "lon" in d.dims and "longitude" not in d.dims:
                rename_map["lon"] = "longitude"
            if rename_map:
                d = d.rename(rename_map)
            ds_list.append(d)
        ds = xr.merge(ds_list, compat="override", combine_attrs="drop_conflicts")

    merged_path = os.path.splitext(zip_path)[0]
    ds.to_netcdf(merged_path)
    ds.close()

    if cleanup:
        shutil.rmtree(extract_dir, ignore_errors=True)
        # keep the .zip for provenance; delete if you prefer:
        # os.remove(zip_path)

    return merged_path
