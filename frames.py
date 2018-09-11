from enum import Enum

class DataUtcReport():
    def __init__(self, timestamp):
        self.time = timestamp
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
        self.mean_sea_level_pressure = None
        self.soil_temperature_10 = None
        self.soil_temperature_30 = None
        self.soil_temperature_00 = None

class DataUtcEnviron():
    def __init__(self, timestamp):
        self.time = timestamp
        self.enclosure_temperature = None
        self.cpu_temperature = None

class DbTable(Enum):
    REPORTS = 1
    ENVREPORTS = 2
    DAYSTATS = 3