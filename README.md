# ERA5_extraction

Extract ERA5 reanalysis data from the Copernicus Climate Data Store (CDS) API and produce plots and statistics for oceanographic
research campaigns. There are two workflows:

1. **Single-site timeseries** — a long hourly record at a point, with monthly climatology, histograms, and wave statistics.
2. **Regional gridded maps** — hourly fields over a region and date range, with map plots and animations.

Scripts are written for VSCode IPython interactive mode: run them cell by cell (`# %%`). Each script `chdir`s to
`~/Python/ERA5_extraction/src`, so clone the repo to `~/Python/ERA5_extraction`.

---

## Setup

### 1. Create the Python environment

The environment is defined in `environment.yml` (conda-forge, Python 3.9). With [mamba](https://mamba.readthedocs.io/)
(or `conda`, which takes the same arguments):

```bash
cd ~/Python/ERA5_extraction
mamba env create -f environment.yml          # creates an environment named ERA5_extraction
mamba activate ERA5_extraction
```

To use a different name, add `-n my_env_name` to the `create` command. To update an existing environment after
`environment.yml` changes:

```bash
mamba env update -f environment.yml --prune
```

In VSCode, select the environment as the Python interpreter / Jupyter kernel before running cells.

Packages: numpy, pandas, xarray, netcdf4, matplotlib, basemap (+ hi-res coastlines), cdsapi, tqdm, ffmpeg (for movies),
ipykernel and ipympl (interactive figures in VSCode).

The older campaign extraction scripts (`ERA5_NORSE_map_extraction.py`, `ERA5_ASTRAL_map_extraction.py`,
`ERA5_SMODE_IOP1_map_extraction.py`) also import `Tom_tools_v1` from `~/Python/Tom_tools`, used only for `tic()`/`toc()`
timing. The current scripts do not need it.

### 2. Configure the CDS API key

A `~/.cdsapirc` file is required before any data can be downloaded. Create a CDS account, accept the ERA5 licence, and copy
your API key from https://cds.climate.copernicus.eu/how-to-api. The file looks like:

```
url: https://cds.climate.copernicus.eu/api
key: <your-personal-access-token>
```

---

## Repository structure

```
ERA5_extraction/
├── src/                      Python scripts (extraction and plotting)
├── data/                     (not tracked by git)
│   └── processed/            Regional gridded NetCDF files
│       ├── tmp/              Monthly download chunks before merging
│       └── timeseries/       Single-site NetCDF, CSV, and text outputs
├── img/                      Output plots and animations (not tracked by git)
└── environment.yml
```

---

## Workflow 1: Single-site timeseries

**Step 1.** Add or select a site in `src/ERA5_timeseries_sites_config.py`. Each entry gives `lon_pt`, `lat_pt`,
`startdate`, `enddate`, and the locator-map half-widths `dx`, `dy`.

**Step 2.** Set `site_name` at the top of `src/ERA5_timeseries_extraction.py` and run it.
- Downloads hourly ERA5 surface met and wave variables at the point from the `reanalysis-era5-single-levels-timeseries`
  dataset (`ERA5_extraction_tool.get_timeseries`)
- Derives wind speed, relative humidity, and downward longwave radiation, and converts units (°C, hPa)
- Raw download: `data/processed/timeseries/ERA5_surface_[SITE]_[YYYY]_[YYYY].nc`
- Processed output: `data/processed/timeseries/ERA5_surface_[SITE]_site_timeseries.nc`

**Step 3.** Set the same `site_name` in `src/ERA5_timeseries_plots_stats.py` and run it. It produces:
- Monthly climatology NetCDF
- Locator map, 5-panel main summary, 4-panel supplemental summary (with monthly climatology overlaid)
- Histograms of wind speed, wave height, and air temperature
- 3×3 monthly climatology grid
- **Wave period and direction by wave-height bin**: for each of 40 H<sub>s</sub> bins, the percent of hours, the median
  and 10–90% range of mean wave period, and the circular mean and spread of mean wave direction, plotted over 2-D
  histograms and saved as CSV
- Text file of extreme wave events (H<sub>s</sub> > 10 m)

Wave variables in the site timeseries are ERA5 `swh` (significant height of combined wind waves and swell), `mwp` (mean
wave period, T<sub>m−1,0</sub>), and `mwd` (mean direction waves come *from*, degrees true).

### Configured sites

| Site | Longitude | Latitude | Date range |
|---|---|---|---|
| RAMA_12N | 88.5°E | 12.0°N | 2000–2026 |
| ASTRAL_2025_Ida | 87.68°E | 13.21°N | 2000–2026 |
| ASTRAL_2025_Kelvin | 87.54°E | 13.21°N | 2000–2026 |
| ASTRAL_2025_Planck | 87.61°E | 13.26°N | 2000–2026 |
| ASTRAL_2025_WHOI43 | 87.61°E | 13.16°N | 2000–2026 |
| Endurance_RCA | 130.2°W | 44.98°N | 2000–2026 |
| SAFARI | 161.0°W | 35.0°N | 2000–Jun 2026 |
| MVCO | 70.50°W | 41.06°N | 2000–Apr 2026 |
| Arabian_Sea | 65.0°E | 15.0°N | 2000–2026 |
| Univ_of_Calabar | 8.36°E | 4.95°N | 2000–2026 |
| Calabar_offshore | 7.0°E | 3.5°N | 2000–2026 |
| Stratus | 85.0°W | 20.0°S | 2000–2026 |

---

## Workflow 2: Regional gridded maps

**Step 1.** In `src/ERA5_map_extraction_2026.py`, add or select a region in `REGIONS` (center `lon0`, `lat0`,
half-widths `dlon`, `dlat`, and start/end year and month), set `REGION = REGIONS['...']`, and run the cells for the
variable groups you need. Each group is downloaded one month at a time (to stay within CDS request limits) and merged:

| Group | Contents | Output file |
|---|---|---|
| `surface` | winds, air/dew-point/skin temperature, SST, pressure, radiation, precipitation | `ERA5_surface_[REGION]_[DATES].nc` |
| `waves` | significant wave height, peak period, mean direction | `ERA5_surface_[REGION]_waves_[DATES].nc` |
| `moisture` | total column water/vapour, vertically integrated moisture flux and divergence | `ERA5_surface_[REGION]_moisture_[DATES].nc` |
| `fluxes` | latent/sensible heat flux, net radiation, evaporation, surface stress | `ERA5_surface_[REGION]_fluxes_[DATES].nc` |

Variable lists for each group are in `VARIABLE_GROUPS` in `src/ERA5_extraction_tool.py`. `[DATES]` is `YYYYMM_YYYYMM`.

**Step 2.** Set `site_name` in `src/ERA5_SAFARI_plots.py` to the region and run it to make map plots (air temperature,
SLP, SST, wave height, column water vapour, moisture transport and divergence) and optional animation frames. Despite
its name, this script handles several regions: SAFARI, SAFARI_2025_2026, Gulf_of_Guinea, Gulf_of_Mexico,
Gulf_of_Mexico_large, NORSE, ASTRAL, and WHOTS.

### Configured regions (`ERA5_map_extraction_2026.py`)

| Region | Center | Period |
|---|---|---|
| ASTRAL_big_2025 | 85°E, 11°N | Apr–Jul 2025 |
| SAFARI | 161°W, 35°N | 2024 |
| SAFARI_2025_2026 | 161°W, 35°N | Oct 2025–Jun 2026 |
| SAFARI_2020_2025 | 161°W, 35°N | 2020–2025 |
| Gulf_of_Guinea | 0°E, 2.5°N | Jan 2010–Jul 2026 |
| Gulf_of_Mexico | 87.5°W, 20°N | Jan 2020–Aug 2026 |
| Gulf_of_Mexico_large | 97.5°W, 32°N | Jan 2020–Aug 2026 |

### Older campaign scripts

These campaign-specific scripts are kept for reference:

| Campaign | Extraction script | Plot script |
|---|---|---|
| NORSE 2023 | `ERA5_NORSE_map_extraction.py` | `ERA5_NORSE_plots.py` |
| ASTRAL 2024 | `ERA5_ASTRAL_map_extraction.py` | `ERA5_ASTRAL_plots.py` |
| ASTRAL 2025 | `ERA5_ASTRAL_map_extraction_2025.py` | `ERA5_ASTRAL_plots_v2.py` |
| S-MODE 2022 | `ERA5_SMODE_IOP1_map_extraction.py` | `ERA5_SMODE_plots.py` |
| SAFARI moisture | `ERA5_SAFARI_moisture_map_extraction.py` | `ERA5_SAFARI_plots.py` |

---

## Key scripts

| Script | Role |
|---|---|
| `ERA5_extraction_tool.py` | CDS request functions, variable groups, monthly download and merge; used by all extraction scripts |
| `ERA5_timeseries_sites_config.py` | Site coordinates, date ranges, and map extents |
| `ERA5_timeseries_extraction.py` | Download and process a single-site hourly timeseries |
| `ERA5_timeseries_plots_stats.py` | Timeseries plots, climatology, histograms, wave statistics, extreme events |
| `ERA5_map_extraction_2026.py` | Download regional gridded ERA5 (surface, waves, moisture, fluxes) |
| `ERA5_SAFARI_plots.py` | Regional map plots and animation frames |

---

## Output files

| File | Description |
|---|---|
| `timeseries/ERA5_surface_[SITE]_site_timeseries.nc` | Processed hourly timeseries with derived variables |
| `timeseries/ERA5_surface_[SITE]_site_monthly_climatology.nc` | Monthly mean climatology |
| `timeseries/ERA5_surface_[SITE]_wave_stats_by_height_bin.csv` | Wave period and direction statistics per H<sub>s</sub> bin |
| `timeseries/ERA5_surface_[SITE]_wave_height_gt10m.txt` | Extreme wave event list (CSV format) |
| `ERA5_surface_[REGION]_[DATES].nc` (and `_waves_`, `_moisture_`, `_fluxes_`) | Regional gridded fields |
| `img/[SITE]_*.png` | Locator map, timeseries summaries, histograms, climatology, wave statistics, maps |

Each gridded download also writes a `*_README.txt` next to the NetCDF file recording when and how it was created.

---

## Links

- CDS account and API key: https://cds.climate.copernicus.eu/how-to-api
- ERA5 single-levels dataset: https://cds.climate.copernicus.eu/datasets/reanalysis-era5-single-levels
- ERA5 point timeseries dataset: https://cds.climate.copernicus.eu/datasets/reanalysis-era5-single-levels-timeseries
- CDS request queue: https://cds.climate.copernicus.eu/requests
