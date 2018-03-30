class DataUtcReport():
    def __init__(self):
        self.time = None
        self.air_temperature = None
        self.exposed_temperature = None
        self.relative_humidity = None
        self.dew_point = None
        self.wind_speed = None
        self.wind_direction = None
        self.wind_gust = None
        self.sunshine_duration = None
        self.rainfall = None
        self.station_pressure = None
        self.pressure_tendency = None
        self.mean_sea_level_pressure = None
        self.soil_temperature_10 = None
        self.soil_temperature_30 = None
        self.soil_temperature_00 = None

class DataUtcEnviron():
    def __init__(self):
        self.time = None
        self.enclosure_temperature = None
        self.cpu_temperature = None

class DataLocalStat():
    def __init__(self):
        self.date = None
        self.air_temperature_min = None
        self.air_temperature_max = None
        self.air_temperature_avg = None
        self.relative_humidity_min = None
        self.relative_humidity_max = None
        self.relative_humidity_avg = None
        self.dew_point_min = None
        self.dew_point_max = None
        self.dew_point_avg = None
        self.wind_speed_min = None
        self.wind_speed_max = None
        self.wind_speed_avg = None
        self.wind_direction_min = None
        self.wind_direction_max = None
        self.wind_direction_avg = None
        self.wind_gust_min = None
        self.wind_gust_max = None
        self.wind_gust_avg = None
        self.sunshine_duration_ttl = None
        self.rainfall_ttl = None
        self.mean_sea_level_pressure_min = None
        self.mean_sea_level_pressure_max = None
        self.mean_sea_level_pressure_avg = None
        self.soil_temperature_10_min = None
        self.soil_temperature_10_max = None
        self.soil_temperature_10_avg = None
        self.soil_temperature_30_min = None
        self.soil_temperature_30_max = None
        self.soil_temperature_30_avg = None
        self.soil_temperature_00_min = None
        self.soil_temperature_00_max = None
        self.soil_temperature_00_avg = None