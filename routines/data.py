import math
import os
from enum import Enum

import sqlite3

import routines.config as config
import routines.helpers as helpers


def create_database(file_path):
    """ Creates a new database and inserts the empty tables
    """
    with sqlite3.connect(file_path) as database:
        cursor = database.cursor()

        cursor.execute("CREATE TABLE reports (Time TEXT PRIMARY KEY NOT NULL, "
            + "AirT REAL, ExpT REAL, RelH REAL, DewP REAL, WSpd REAL, WDir "
            + "INTEGER, WGst REAL, SunD INTEGER, Rain REAL, StaP REAL, MSLP "
            + "REAL, ST10 REAL, ST30 REAL, ST00 REAL)")
        cursor.execute("CREATE TABLE envReports (Time TEXT PRIMARY KEY NOT "
            + "NULL, EncT REAL, CPUT REAL)")

        QUERY = ("CREATE TABLE dayStats (Date TEXT PRIMARY KEY NOT NULL, "
            + "{0}AirT_Avg REAL, AirT_Min REAL, AirT_Max REAL, RelH_Avg REAL, "
            + "RelH_Min REAL, RelH_Max REAL, DewP_Avg REAL, DewP_Min REAL, "
            + "DewP_Max REAL, WSpd_Avg REAL, WSpd_Min REAL, WSpd_Max REAL, "
            + "WDir_Avg INTEGER, WDir_Min INTEGER, WDir_Max INTEGER, WGst_Avg "
            + "REAL, WGst_Min REAL, WGst_Max REAL, SunD_Ttl INTEGER, Rain_Ttl "
            + "REAL, MSLP_Avg REAL, MSLP_Min REAL, MSLP_Max REAL, ST10_Avg "
            + "REAL, ST10_Min REAL, ST10_Max REAL, ST30_Avg REAL, ST30_Min "
            + "REAL, ST30_Max REAL, ST00_Avg REAL, ST00_Min REAL, ST00_Max "
            + "REAL)")

        # Upload database needs to discern every dayStat record update
        if file_path == config.upload_db_path:
            cursor.execute(QUERY.format("Signature TEXT NOT NULL, "))
        else: cursor.execute(QUERY.format(""))

        # Upload database needs to keep track of uploaded camera images
        if file_path == config.upload_db_path:
            cursor.execute("CREATE TABLE camReports (Time TEXT PRIMARY KEY NOT "
            + "NULL)")

        database.commit()

def query_database(db_path, query, values):
    """ Runs a query on the database using a prepared statement with the
        specified values
    """
    if not os.path.isfile(db_path): return False

    # Check space before performing any write queries
    if (query.startswith("INSERT") or query.startswith("UPDATE")
        or query.startswith("DELETE")):

        free_space = helpers.remaining_space(config.data_directory)
        if free_space == None or free_space < 0.1: return False

    if values == None: values = ()

    try:
        with sqlite3.connect(db_path) as database:
            database.row_factory = sqlite3.Row
            cursor = database.cursor()
            cursor.execute(query, values)

            if (query.startswith("INSERT") or query.startswith("UPDATE")
                or query.startswith("DELETE")):
                return True

            result = cursor.fetchall()
            if len(result) == 0: return None
            return result

    except: return False

def calculate_dew_point(AirT, RelH):
    """ Calculates dew point using the same formula the Met Office uses
    """
    if AirT == None or RelH == None: return None

    DewP_a = 0.4343 * math.log(RelH / 100)
    DewP_b = ((8.082 - AirT / 556.0) * AirT)
    DewP_c = DewP_a + (DewP_b) / (256.1 + AirT)
    DewP_d = math.sqrt((8.0813 - DewP_c) ** 2 - (1.842 * DewP_c))

    return 278.04 * ((8.0813 - DewP_c) - DewP_d)

def calculate_mslp(StaP, AirT, DewP):
    """ Reduces station pressure to mean sea level using the WMO formula
    """
    if StaP == None or AirT == None or DewP == None: return None

    MSLP_a = 6.11 * 10 ** ((7.5 * DewP) / (237.3 + DewP))
    MSLP_b = (9.80665 / 287.3) * config.aws_elevation
    MSLP_c = ((0.0065 * config.aws_elevation) / 2) 
    MSLP_d = AirT + 273.15 + MSLP_c + MSLP_a * 0.12
    
    return StaP * math.exp(MSLP_b / MSLP_d)


class ReportFrame():
    def __init__(self, time):
        self.time = time
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

class EnvReportFrame():
    def __init__(self, time):
        self.time = time
        self.enclosure_temperature = None
        self.cpu_temperature = None

class DbTable(Enum):
    REPORTS = 1
    ENVREPORTS = 2
    DAYSTATS = 3