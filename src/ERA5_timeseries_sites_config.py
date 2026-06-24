"""
Site configuration for ERA5 timeseries extraction and plotting scripts.

Add new sites here; both ERA5_timeseries_extraction.py and
ERA5_timeseries_plots_stats.py import from this file.

Keys per site:
    lon_pt, lat_pt  : site coordinates (degrees E, degrees N)
    startdate       : ERA5 download start date ('YYYY-MM-DD')
    enddate         : ERA5 download end date   ('YYYY-MM-DD')
    dx, dy          : map half-extent in degrees (used by plots_stats locator map)
"""

SITES = {
    'RAMA_12N': dict(
        lon_pt=88.5,    lat_pt=12.0,
        startdate='2000-01-01', enddate='2026-01-01',
        dx=20, dy=15,
    ),
    'ASTRAL_2025_Ida': dict(
        lon_pt=87.68,   lat_pt=13.21,
        startdate='2000-01-01', enddate='2026-01-01',
        dx=10, dy=10,
    ),
    'ASTRAL_2025_Kelvin': dict(
        lon_pt=87.54,   lat_pt=13.21,
        startdate='2000-01-01', enddate='2026-01-01',
        dx=10, dy=10,
    ),
    'ASTRAL_2025_Planck': dict(
        lon_pt=87.61,   lat_pt=13.26,
        startdate='2000-01-01', enddate='2026-01-01',
        dx=10, dy=10,
    ),
    'ASTRAL_2025_WHOI43': dict(
        lon_pt=87.61,   lat_pt=13.16,
        startdate='2000-01-01', enddate='2026-01-01',
        dx=10, dy=10,
    ),
    'Endurance_RCA': dict(
        lon_pt=-130.2,  lat_pt=44.98,
        startdate='2000-01-01', enddate='2026-01-01',
        dx=20, dy=15,
    ),
    'SAFARI': dict(
        lon_pt=-161,    lat_pt=35,
        startdate='2000-01-01', enddate='2026-06-21',
        dx=60, dy=25,
    ),
    'MVCO': dict(
        lon_pt=-70.4951,    lat_pt=41.0614,
        startdate='2000-01-01', enddate='2026-04-01',
        dx=10, dy=10,
    ),
    'Arabian_Sea': dict(
        lon_pt=65,    lat_pt=15,
        startdate='2000-01-01', enddate='2026-01-01',
        dx=30, dy=20,
    ),
}
