Written using ERA5_extraction_tool.get_surface_vars() on 
2024-08-30 11:49:32.234776
 Invoked from /home/jtomf/miniforge3/envs/NORSE_ASTRAL/lib/python3.9/site-packages/ipykernel_launcher.py


JTF note 2024-08-31:
CDS-beat API is not working, but this would be the API query:

import cdsapi

c = cdsapi.Client()

c.retrieve(
    'reanalysis-era5-single-levels',
    {
        'product_type': 'reanalysis',
        'variable': [
            '10m_u_component_of_wind', '10m_v_component_of_wind', '2m_dewpoint_temperature',
            '2m_temperature', 'mean_sea_level_pressure', 'mean_wave_direction',
            'mean_wave_period', 'sea_surface_temperature', 'significant_height_of_combined_wind_waves_and_swell',
            'surface_net_solar_radiation', 'surface_net_thermal_radiation', 'surface_pressure',
            'surface_solar_radiation_downwards', 'surface_thermal_radiation_downwards', 'total_precipitation',
        ],
        'year': '2023',
        'month': [
            '10', '11', '12',
        ],
        'day': [
            '01', '02', '03',
            '04', '05', '06',
            '07', '08', '09',
            '10', '11', '12',
            '13', '14', '15',
            '16', '17', '18',
            '19', '20', '21',
            '22', '23', '24',
            '25', '26', '27',
            '28', '29', '30',
            '31',
        ],
        'time': [
            '00:00', '01:00', '02:00',
            '03:00', '04:00', '05:00',
            '06:00', '07:00', '08:00',
            '09:00', '10:00', '11:00',
            '12:00', '13:00', '14:00',
            '15:00', '16:00', '17:00',
            '18:00', '19:00', '20:00',
            '21:00', '22:00', '23:00',
        ],
        'area': [
            80, -13, 60,
            7,
        ],
        'format': 'netcdf',
    },
    'download.nc')
