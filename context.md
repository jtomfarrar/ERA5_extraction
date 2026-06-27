<!-- PROGRESS: active-file=src/ERA5_SAFARI_plots.py -->

# ERA5 Extraction Context

## Current Focus

Generalizing `src/ERA5_SAFARI_plots.py` so it can make maps and movies for multiple ERA5 extraction sites while preserving the existing interactive-script workflow.

The current active configuration in the plotting script is:

- `site_name = 'SAFARI_2025_2026'`
- `var = 'atmp'`

## Important Decisions

- Keep the existing `elif site_name == ...` site configuration style rather than introducing a site configuration dictionary.
- Use `suffix` for optional filename suffixes, not `date_label`.
- Only `SAFARI_2025_2026` currently uses `suffix = '_202510_202606'`; other site branches use `suffix = ''`.
- Use `lon0` and `lat0` for the extracted map-domain center, consistent with `src/ERA5_map_extraction_2026.py`.
- Use `lon_pt` and `lat_pt` for the plotted site marker or mooring location.
- For `SAFARI_2025_2026`, the extracted domain center is `lon0 = -161`, `lat0 = 35`, while the actual mooring marker is `lon_pt = -158`, `lat_pt = 33.44`.
- The current larger `SAFARI_2025_2026` extraction uses `dx = 48`, `dy = 25` in the plotting script, matching `dlon = 48`, `dlat = 25` in `src/ERA5_map_extraction_2026.py`.
- Where the marker and domain center are the same, define `lon_pt = lon0` and `lat_pt = lat0` rather than repeating numeric values.

## Files

- `src/ERA5_SAFARI_plots.py`: active plotting and movie-generation script.
- `src/ERA5_map_extraction_2026.py`: extraction script whose region definitions and filename conventions should guide the plotting script.
- `src/ERA5_extraction_tool.py`: defines ERA5 variable request groups, including the moisture variables.

## File Naming

The plotting script now builds filenames this way:

- Surface: `ERA5_surface_{site_name}{suffix}.nc`
- Waves: `ERA5_surface_{site_name}_waves{suffix}.nc`
- Moisture: `ERA5_surface_{site_name}_moisture{suffix}.nc`
- Fluxes: `ERA5_surface_{site_name}_fluxes{suffix}.nc`

Movie frames are written to a site- and variable-specific directory:

- `../img/movie_frames_{site_name}_{var}/`

Movie output is written as:

- `../img/{site_name}_{var}_out.mp4`

## Moisture Data Notes

The moisture file for `SAFARI_2025_2026` is:

- `data/processed/ERA5_surface_SAFARI_2025_2026_moisture_202510_202606.nc`

Important variable names in that file:

- `tcwv`: total column water vapour, units `kg m**-2`
- `viwve`: vertically integrated eastward water vapour flux, units `kg m**-1 s**-1`
- `viwvn`: vertically integrated northward water vapour flux, units `kg m**-1 s**-1`
- `vimdf`: vertically integrated divergence of moisture flux, units `kg m**-2 s**-1`

`plot_TCWV()` uses `tcwv` as filled contours and overlays vectors from `viwve` and `viwvn`.

`plot_IVT()` uses `sqrt(viwve**2 + viwvn**2)` as filled contours and overlays vectors from `viwve` and `viwvn`.

`plot_VIMDF()` uses `vimdf * 86400` as filled contours, converting from `kg m**-2 s**-1` to `kg m**-2 day**-1`, and overlays the same IVT vectors.

## Surface Flux Data Notes

The surface flux file pattern is:

- `data/processed/ERA5_surface_{site_name}_fluxes{suffix}.nc`

The planned/current `SAFARI_2025_2026` flux file is:

- `data/processed/ERA5_surface_SAFARI_2025_2026_fluxes_202510_202606.nc`

Important expected variable names:

- `e`: evaporation, expected units `m` water equivalent, typically negative for evaporation in ERA5.
- `tp`: total precipitation, expected units `m`.

`plot_evap_rate()` uses positive evaporation convention:

- `evap_rate = -e * 1000 * 24`
- overlays vertically integrated water vapour flux vectors from `viwve` and `viwvn`.

`plot_EMP()` uses:

- `evap_rate = -e * 1000 * 24`
- `precip_rate = tp * 1000 * 24`
- `emp = evap_rate - precip_rate`
- overlays vertically integrated water vapour flux vectors from `viwve` and `viwvn`.

These conversions assume hourly ERA5 accumulations and produce approximate rates in `mm day**-1`.

## Domain Notes

For the earlier `SAFARI_2025_2026` surface file:

- `data/processed/ERA5_surface_SAFARI_2025_2026_202510_202606.nc`

has this domain:

- Latitude: 55 to 15 degrees north, decreasing
- Longitude: -201 to -121 degrees east
- Grid spacing: 0.25 degrees
- Grid size: 161 latitude by 321 longitude

The wave file has the same extent but uses 0.5 degree spacing, with 81 latitude by 161 longitude.

The updated `SAFARI_2025_2026` extraction settings are `lon0 = -161`, `lat0 = 35`, `dlon = 48`, `dlat = 25`. The corresponding plotted/extracted domain is:

- Latitude: 10 to 60 degrees north
- Longitude: -209 to -113 degrees east
- Surface grid size if using 0.25 degree spacing: 201 latitude by 385 longitude
- Wave grid size if using 0.5 degree spacing: 101 latitude by 193 longitude

## CDS API / ERA5 Downloads

Official references:

- ECMWF Confluence ERA5 download guide: https://confluence.ecmwf.int/spaces/CKB/pages/129135000/How+to+download+ERA5
- CDS API setup page: https://cds.climate.copernicus.eu/how-to-api
- CDS request queue: https://cds.climate.copernicus.eu/requests

The CDS API requires a Copernicus/CDS account and a local `$HOME/.cdsapirc` file containing the API URL and personal access token. Do not commit credentials or tokens to this repository.

The official CDS API setup page shows the current Linux setup pattern:

```text
url: https://cds.climate.copernicus.eu/api
key: <PERSONAL-ACCESS-TOKEN>
```

The project uses the Python `cdsapi` client through `src/ERA5_extraction_tool.py`. The helper currently retrieves from:

- `ERA5_SINGLE_LEVELS_DATASET`
- DOI noted in code: `10.24381/cds.adbb2d47`

The main request pattern is in `extract_vars_single_month()`:

- Creates `c = cdsapi.Client()`.
- Calls `c.retrieve(...)`.
- Uses `product_type = 'reanalysis'`.
- Uses all days and all hours for the selected month.
- Uses `area = build_area(lon0, lat0, dlon, dlat)`.
- Requests NetCDF output with `format = 'netcdf'` and `download_format = 'unarchived'`.

CDS `area` order is important:

- `area = [north, west, south, east]`
- In this project, `build_area(lon0, lat0, dlon, dlat)` converts center/half-width coordinates into that CDS order.

For large date ranges, use `extract_monthly_range()` rather than requesting the whole period in one CDS request. It downloads one month at a time, writes monthly temporary files, then merges them with `xarray.open_mfdataset(..., combine='by_coords', engine='h5netcdf')` and writes a compressed NetCDF with `h5netcdf`.

The extraction script `src/ERA5_map_extraction_2026.py` defines project regions using:

- `region_name`
- `lon0`, `lat0`
- `dlon`, `dlat`
- `start_year`, `start_month`
- `end_year`, `end_month`
- `out_path`

Current variable groups in `src/ERA5_extraction_tool.py`:

- `surface`: 10 m winds, 2 m temperature/dewpoint, skin temperature, pressures, SST, radiation, precipitation.
- `waves`: peak wave period, significant wave height, mean wave direction.
- `moisture`: mean sea level pressure, surface pressure, moisture flux divergence, eastward/northward water vapour flux, total column water, total column water vapour.
- `fluxes`: surface radiation, precipitation, skin temperature, turbulent fluxes, evaporation.

When CDS returns a ZIP instead of a plain NetCDF, `_ensure_netcdf_from_cds()` is intended to unpack and merge the NetCDF parts into a readable merged file.

Operational notes:

- Check the CDS queue at https://cds.climate.copernicus.eu/requests for long-running downloads.
- Keep `cleanup_tmp=False` when debugging monthly extraction failures so intermediate monthly files remain available.
- Set `cleanup_tmp=True` when the monthly workflow is stable to remove temporary files after merge.
- Before running project-specific CDS download commands, ask which mamba environment should be used, per `../AGENTS.md`.

GRIB-vs-NetCDF test notes:

- ECMWF forum note on NetCDF ERA5 request limits: https://forum.ecmwf.int/t/limitation-change-on-netcdf-era5-requests/12477
- GRIB requests may permit larger ERA5 selections than NetCDF requests because ERA5 is archived natively as GRIB and NetCDF requires additional CDS-side conversion/post-processing.
- The ECMWF forum guidance suggests checking request feasibility in the CDS web form before updating API scripts when request-size limits are uncertain.
- A tiny ERA5 GRIB request downloaded successfully using `data_format = 'grib'`.
- `cfgrib` and `eccodes` were installed into the `NORSE_ASTRAL` mamba environment for testing.
- A simple one-variable GRIB file converted to NetCDF successfully with both xarray/cfgrib and `grib_to_netcdf`.
- A mixed GRIB request containing `2m_temperature`, `total_precipitation`, and `surface_solar_radiation_downwards` exposed an important caveat:
  - Plain `xr.open_dataset(..., engine='cfgrib')` opened only `t2m` and skipped the accumulated variables.
  - `cfgrib.open_datasets(...)` split the file into an instant dataset (`t2m`) and an accumulated dataset (`tp`, `ssrd`).
  - `grib_to_netcdf` converted all three variables into one NetCDF file.
- The same mixed request sent to CDS as NetCDF returned a ZIP file containing two NetCDF files split by `stepType`: one instant file and one accumulated file.
- Both CDS NetCDF split files had the same `valid_time`, but retained GRIB metadata such as `GRIB_stepType` as variable attributes.
- The default `grib_to_netcdf` output had one `time` coordinate and all variables in one file, but did not preserve richer GRIB metadata such as `GRIB_stepType`, forecast reference time, `step`, or `valid_time`.
- Current decision: do not switch the extraction workflow to GRIB conversion yet. Continue with monthly NetCDF downloads for now, and revisit GRIB only if CDS NetCDF request limits become a blocker.

## Current Plot Modes

The plotting script dispatches these values of `var`:

- `atmp`: 2 m air temperature filled contours with 10 m wind vectors.
- `slp`: sea level pressure filled contours with 10 m wind vectors.
- `sst`: sea surface temperature filled contours with 10 m wind vectors.
- `swh`: significant wave height filled contours with 10 m wind vectors.
- `tcwv`: total column water vapour filled contours with IVT vectors.
- `ivt`: IVT magnitude filled contours with IVT vectors.
- `vimdf`: moisture flux divergence filled contours with IVT vectors.
- `evap`: positive evaporation rate filled contours with IVT vectors.
- `emp`: evaporation minus precipitation filled contours with IVT vectors.

For moisture plot modes, `time = ERA_moisture.valid_time`; for flux plot modes that overlay IVT vectors, `ERA_fluxes` is restricted to `ERA_moisture.valid_time`; otherwise `time = ERA.valid_time`.

The bottom min-MSL/max-wind diagnostic plot uses `time_met = ERA.valid_time` so it does not fail when the active moisture-file time axis has a different length.

## Open Issues

- Tune `vimdf` contour levels and sign convention. Current levels are `np.arange(-40,42,2)` after converting to `kg m**-2 day**-1`.
- Confirm whether `RdBu_r` is the preferred colormap for moisture flux divergence.
- Consider making the bottom min-MSL/max-wind diagnostic optional, especially for moisture-only movie generation.
- Consider skipping the surface `ERA` file load for pure moisture plots if the bottom diagnostic is disabled.
- `plot_time = np.datetime64('2026-01-15T00:00:00')` is currently repeated in all site branches and may not exist for older files.
- `lcc_params` is generalized but appears unused by the current plotting functions.

## Validation

After the latest edits, this command passed:

```bash
python -m py_compile src/ERA5_map_extraction_2026.py src/ERA5_SAFARI_plots.py
```

The full plotting/movie workflow has not been run by the agent because it depends on the project mamba environment and does substantial plotting and `ffmpeg` work. The user has run the script in the `NORSE_ASTRAL` environment.
