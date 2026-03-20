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

@author: jtomf
"""
import cdsapi
import datetime
import sys
import time
import os, zipfile, glob, tempfile, shutil
import xarray as xr

# N, W, S, E valid range is 90, -180, -90, 180
# could use lon0=0 lat0=0 dlon=180 dlat=90

# E-W valid range is -180, 180
#lon0 = -158 # NORSE=3, WHOTS=-158
#lat0 = 22.67 # NORSE=70, WHOTS=22.67
#dlat = 5
#dlon = 5
#yr = '2011'

def get_timeseries(lon0, lat0, startdate, enddate, output_file=None):
    '''
    Extract ERA5 timeseries data using Copernicus Climate Data System API.  
    Given a geographic location and a date range, saves file 'outfile.nc' in local directory

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

def get_surface_vars(lon0,lat0,dlon,dlat,yr,mm,output_file=None):
    '''
    Extract ERA5 surface data using Copernicus Climate Data System API.  
    Given a geographic region and a year, saves file 'ERA5_{lon0}E_{lat0}N_{yr}.nc' in local directory

    Parameters
    ----------
    lon0 : numeric
        Target longitude.
    lat0 : numeric
        Target latitude.
    dlon : numeric
        +/- latitude range around lon0.
    dlat : numeric
        +/- latitude range around lat0.
    yr : str
        Year to extract.
    region_name (optional) : str 
        If provided, output filename is ERA5_surface_{region_name}_{yr}.nc (i.e., region_name + '_' + yr +'.nc')
        If not provided, output fileanme is 'ERA5_surface_{lon0}E_{lat0}N_{yr}.nc'

    Returns
    -------
    None, but saves output file in local directory.
    'ERA5_{lon0}E_{lat0}N_{yr}.nc'

    '''
    if output_file is None:
        output_file = 'outfile.nc'

    c = cdsapi.Client()
    c.retrieve(
        'reanalysis-era5-single-levels', # DOI: 10.24381/cds.adbb2d47
        {
            'product_type': 'reanalysis',
            'variable': [
                '10m_u_component_of_wind', '10m_v_component_of_wind', '2m_dewpoint_temperature', 'skin_temperature',
                '2m_temperature', 'mean_sea_level_pressure', 'sea_surface_temperature', 
                'surface_net_solar_radiation', 'surface_net_thermal_radiation', 'surface_pressure',
                'surface_solar_radiation_downwards', 'surface_thermal_radiation_downwards', 'total_precipitation',
            ], #'mean_wave_direction', 'mean_wave_period', 'significant_height_of_combined_wind_waves_and_swell',
            'year': yr,
            'month': mm, #[#'01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12',],
            'day': [
                '01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12', '13', '14', '15', '16', '17', '18', 
                '19', '20', '21', '22', '23', '24', '25', '26', '27', '28', '29', '30', '31',
            ],
            'time': [
                '00:00', '01:00', '02:00', '03:00', '04:00', '05:00', '06:00', '07:00', '08:00', '09:00', '10:00', '11:00',
                '12:00', '13:00', '14:00', '15:00', '16:00', '17:00', '18:00', '19:00', '20:00', '21:00', '22:00', '23:00',
            ],
            # area is N, W, S, E; valid range is 90, -180, -90, 180
            'area': [
                lat0+dlat, lon0-dlon, lat0-dlat,
                lon0+dlon,
            ],
            'format': 'netcdf',
            "download_format": "unarchived",
        },
        output_file)

    final_path = _ensure_netcdf_from_cds(output_file)
    print(f"Surface data saved at: {final_path}")

    # Write a readme file to say when and by what script the file was written
    calling_fname = str(sys.argv[0])
    output_file_prefix = output_file[:-3]
    ReadmeFile = open(output_file_prefix+"_README.txt", "w")
    ReadmeFile.write ('Written using ERA5_extraction_tool.get_surface_vars() on \n' + str(datetime.datetime.now()) + 
                      '\n Invoked from ' + calling_fname) 
    ReadmeFile.close()

def get_wave_vars(lon0,lat0,dlon,dlat,yr,mm,output_file=None):
    '''
    Extract ERA5 surface wave data using Copernicus Climate Data System API.  
    Given a geographic region and a year, saves file 'ERA5_{lon0}E_{lat0}N_{yr}.nc' in local directory

    Parameters
    ----------
    lon0 : numeric
        Target longitude.
    lat0 : numeric
        Target latitude.
    dlon : numeric
        +/- latitude range around lon0.
    dlat : numeric
        +/- latitude range around lat0.
    yr : str
        Year to extract.
    region_name (optional) : str 
        If provided, output filename is ERA5_surface_{region_name}_{yr}.nc (i.e., region_name + '_' + yr +'.nc')
        If not provided, output fileanme is 'ERA5_surface_{lon0}E_{lat0}N_{yr}.nc'

    Returns
    -------
    None, but saves output file in local directory.
    'ERA5_{lon0}E_{lat0}N_{yr}.nc'

    '''
    if output_file is None:
        output_file = 'outfile.nc'

    c = cdsapi.Client()
    c.retrieve(
        'reanalysis-era5-single-levels', # DOI: 10.24381/cds.adbb2d47
        {
            'product_type': 'reanalysis',
            'variable': [
            #'coefficient_of_drag_with_waves', 'mean_direction_of_total_swell', 'mean_direction_of_wind_waves',
            #'mean_period_of_total_swell', 'mean_period_of_wind_waves', 'mean_wave_direction',
            #'mean_wave_period', 'mean_wave_period_based_on_first_moment', 'mean_wave_period_based_on_first_moment_for_swell',
            #'mean_wave_period_based_on_first_moment_for_wind_waves', 'ocean_surface_stress_equivalent_10m_neutral_wind_direction', 'ocean_surface_stress_equivalent_10m_neutral_wind_speed',
            'peak_wave_period', 'significant_height_of_combined_wind_waves_and_swell','mean_wave_direction',
            ], 
            'year': yr,
            'month': mm, #[#'01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12',],
            'day': [
                '01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12', '13', '14', '15', '16', '17', '18', 
                '19', '20', '21', '22', '23', '24', '25', '26', '27', '28', '29', '30', '31',
            ],
            'time': [
                '00:00', '01:00', '02:00', '03:00', '04:00', '05:00', '06:00', '07:00', '08:00', '09:00', '10:00', '11:00',
                '12:00', '13:00', '14:00', '15:00', '16:00', '17:00', '18:00', '19:00', '20:00', '21:00', '22:00', '23:00',
            ],
            # area is N, W, S, E; valid range is 90, -180, -90, 180
            'area': [
                lat0+dlat, lon0-dlon, lat0-dlat,
                lon0+dlon,
            ],
            'format': 'netcdf',
            "download_format": "unarchived",
        },
        output_file)

    final_path = _ensure_netcdf_from_cds(output_file)
    print(f"Wave data saved at: {final_path}")

    # Write a readme file to say when and by what script the file was written
    calling_fname = str(sys.argv[0])
    # strip off .nc from output_file
    output_file_prefix = output_file[:-3]
    ReadmeFile = open(output_file_prefix+"_README.txt", "w")
    ReadmeFile.write ('Written using ERA5_extraction_tool.get_wave_vars() on \n' + str(datetime.datetime.now()) + 
                      '\n Invoked from ' + calling_fname) 
    ReadmeFile.close()

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
