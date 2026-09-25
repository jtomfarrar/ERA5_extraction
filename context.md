<!-- PROGRESS: active-file=src/ERA5_SAFARI_plots.py -->

# ERA5 Extraction Context

## Current Focus

Generalizing `src/ERA5_SAFARI_plots.py` so it can make maps and movies for multiple ERA5 extraction sites while preserving the existing interactive-script workflow.

The current active configuration in the plotting script is:

- `site_name = 'Gulf_of_Mexico'`
- `var = 'swh'`

Recent work has moved to Gulf of Mexico / Mississippi basin domains; see Domain Notes.

## Important Decisions

- Keep the existing `elif site_name == ...` site configuration style rather than introducing a site configuration dictionary.
- Use `suffix` for optional filename suffixes, not `date_label`.
- Site branches that read date-labelled files set `suffix` accordingly: `SAFARI_2025_2026` uses `'_202510_202606'`, `Gulf_of_Guinea` uses `'_201001_202607'`, `Gulf_of_Mexico` uses `'_202101_202207'`, `Gulf_of_Mexico_large` uses `'_201001_202608'`. Older site branches use `suffix = ''`.
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

### Gulf of Mexico domains

`Gulf_of_Mexico` (`lon0 = -87.5`, `lat0 = 20`, `dlon = 12.5`, `dlat = 15`):

- Latitude: 5 to 35 degrees north
- Longitude: -100 to -75 degrees east
- Surface grid: 121 latitude by 101 longitude at 0.25 degrees
- Wave grid: 61 latitude by 51 longitude at 0.5 degrees
- Data on disk covers 2021-01 to 2022-07 (`_202101_202207`); the region dict in the extraction script has since been changed to 2010-01 to 2026-08, so a re-run would write different filenames.

`Gulf_of_Mexico_large` (`lon0 = -97.5`, `lat0 = 32`, `dlon = 22.5`, `dlat = 18`), added 2026-09-15:

- Latitude: 14 to 50 degrees north
- Longitude: -120 to -75 degrees east
- Surface grid: 145 latitude by 181 longitude at 0.25 degrees
- Wave grid: 73 latitude by 91 longitude at 0.5 degrees
- Chosen to contain all of Mexico (14.5 to 32.7 north, -118.4 to -86.7 east, including Baja and the Yucatan) and the whole Mississippi/Missouri drainage basin (north to about 49.5, west past the Continental Divide in Montana near -113.5, east to the Allegheny headwaters near -77.7).
- The plotting script marker for this site is the Mississippi River mouth at Head of Passes, `lon_pt = -89.25`, `lat_pt = 29.15`.

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

### Request size test, 2026-09-15

One month (2021-08) of the `surface` group was requested for the full `Gulf_of_Mexico_large` domain via `extract_vars_single_month()` to test whether the enlarged domain hits the NetCDF request-size limit.

- Result: accepted, no size rejection. Request ID `c38ca709-e5b9-46d8-b050-c74bb50e92b6`.
- Returned 744 times by 145 latitude by 181 longitude with all 13 surface variables, merged out of the CDS ZIP into one file by `_ensure_netcdf_from_cds()`.
- File size 357 MB; 9.7 minutes wall clock, of which about 50 s queued, 7.5 min CDS processing, and 1.3 min download.
- Conclusion: the NetCDF request-size limit is not a blocker for a 45 by 36 degree domain at 0.25 degrees with monthly chunking, so GRIB conversion is still unnecessary.
- Per-request size is set by the domain and the variable group, not by the date range. Shortening the date range reduces the number of requests, not the size of any one request.
- Fields per monthly request: surface 13 x 744 = 9672, fluxes 8184, moisture 5208, waves 2232.
- Wall clock, not disk, is the binding cost. At roughly 9.7 min per request run serially, 2020-01 to 2026-08 is 320 requests (about 45 to 55 hours) and 2010-01 to 2026-08 is 800 requests (about 110 to 130 hours).
- Test artifacts are in `data/processed/tmp/size_test/`.

### NetCDF compression

- CDS monthly files arrive with deflate level 1 plus the shuffle filter and large chunks (372 x 73 x 91 on the test file), achieving about 2.7x compression over raw float32.
- Merged files previously used deflate 4 with no shuffle, and `ds[var].encoding.clear()` left chunking to the h5netcdf default, which chose long-in-time, tiny-in-space chunks: 433 x 8 x 7 for `Gulf_of_Mexico`, 4541 x 2 x 8 for `Gulf_of_Guinea`. Achieved compression was only about 1.9x.
- Benchmark on the same 200-hour, 13-variable slice of the test file (raw float32 = 273 MB), timing 20 single-time map slices as the plotting functions read them:

```text
current (deflate4, no shuffle)      138.4 MB  1.97x  write 8.6s  20 map slices 0.50s
deflate4 + shuffle                  105.9 MB  2.58x  write 4.5s  20 map slices 0.37s
deflate4 + shuffle + 24h chunks      96.3 MB  2.83x  write 5.6s  20 map slices 0.30s
deflate1 + shuffle + 24h chunks     100.2 MB  2.72x  write 3.9s  20 map slices 0.32s
```

- Change applied 2026-09-15 in `merge_monthly_files()`: encoding now sets `'shuffle': True`, and for 3D variables `chunksizes = (min(24, nt), ny, nx)` so one chunk holds whole maps. `complevel` stays at 4 because write time is not the bottleneck.
- Effect: about 30 percent smaller merged files, faster writes, and about 1.7x faster map-slice reads. Projected `Gulf_of_Mexico_large` totals fall from about 97 GB to about 66 GB for a 2020 start.
- Existing merged files keep the old encoding until they are re-merged.

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
- `_ensure_netcdf_from_cds()` has `os.remove(zip_path)` commented out, so every request leaves a `.nc` and an equal-sized `.nc.zip`. Over a 320-request run that is roughly 30 GB of stray zips in the surface `tmp` directory, which is kept because the surface stream uses `cleanup_tmp=False`.
- `plot_map`, `contour_SLP`, `plot_SST` and `plot_SWH` call `contourf` without `extend=`, so values outside the contour levels are left unfilled rather than flagged. The moisture and flux plotting functions do pass `extend`.
- `plot_SST` contours `skt` (skin temperature, land included) even though the ocean-only `sst` variable is present in the surface files.
- The `surface`, `moisture` and `fluxes` variable groups overlap: `fluxes` repeats six surface variables and `moisture` repeats two, so those fields are downloaded and stored up to three times (roughly 50 GB of duplication on a 200-month `Gulf_of_Mexico_large` run).
- `place_labels` is defined only in some site branches and is read via `if 'place_labels' in globals()`, so labels from a previous site persist when switching sites within one interactive session.

## Validation

After the latest edits, this command passed:

```bash
python -m py_compile src/ERA5_map_extraction_2026.py src/ERA5_SAFARI_plots.py src/ERA5_extraction_tool.py
```

The 2026-09-15 CDS request-size test and the compression benchmark were both run in the `NORSE_ASTRAL` environment.

The full plotting/movie workflow has not been run by the agent because it depends on the project mamba environment and does substantial plotting and `ffmpeg` work. The user has run the script in the `NORSE_ASTRAL` environment.
