import math
import os
from datetime import timedelta
from enum import Enum

import sqlite3

import routines.config as config
import routines.helpers as helpers


def create_database(file_path):
    with sqlite3.connect(file_path) as database:
        cursor = database.cursor()

        cursor.execute("CREATE TABLE reports (Time TEXT PRIMARY KEY NOT NULL, "
            + "AirT REAL, ExpT REAL, RelH REAL, DewP REAL, WSpd REAL, WDir "
            + "INTEGER, WGst REAL, SunD INTEGER, Rain REAL, StaP REAL, MSLP "
            + "REAL, ST10 REAL, ST30 REAL, ST00 REAL)")
        cursor.execute("CREATE TABLE envReports (Time TEXT PRIMARY KEY NOT "
            + "NULL, EncT REAL, CPUT REAL)")
        cursor.execute("CREATE TABLE dayStats (Date TEXT PRIMARY KEY NOT NULL, "
            + "AirT_Avg REAL, AirT_Min REAL, AirT_Max REAL, RelH_Avg REAL, "
            + "RelH_Min REAL, RelH_Max REAL, DewP_Avg REAL, DewP_Min REAL, "
            + "DewP_Max REAL, WSpd_Avg REAL, WSpd_Min REAL, WSpd_Max REAL, "
            + "WDir_Avg INTEGER, WDir_Min INTEGER, WDir_Max INTEGER, WGst_Avg "
            + "REAL, WGst_Min REAL, WGst_Max REAL, SunD_Ttl INTEGER, Rain_Ttl "
            + "REAL, MSLP_Avg REAL, MSLP_Min REAL, MSLP_Max REAL, ST10_Avg "
            + "REAL, ST10_Min REAL, ST10_Max REAL, ST30_Avg REAL, ST30_Min "
            + "REAL, ST30_Max REAL, ST00_Avg REAL, ST00_Min REAL, ST00_Max "
            + "REAL)")

        database.commit()

def read_record(table, time):
    """ Query the database for a record in the specified table matching the
        specified time
    """
    if not os.path.isfile(config.database_path): return False

    try:
        with sqlite3.connect(config.database_path) as database:
            database.row_factory = sqlite3.Row
            cursor = database.cursor()

            if table == DbTable.REPORTS:
                cursor.execute("SELECT * FROM reports WHERE Time = ?",
                                (time.strftime("%Y-%m-%d %H:%M:%S"),))
            elif table == DbTable.ENVREPORTS:
                cursor.execute("SELECT * FROM envReports WHERE Time = ?",
                                (time.strftime("%Y-%m-%d %H:%M:%S"),))
            elif table == DbTable.DAYSTATS:
                cursor.execute("SELECT * FROM dayStats WHERE Date = ?",
                                (time.strftime("%Y-%m-%d"),))

            return cursor.fetchone()
    except: return False

def write_record(table, data):
    """ Writes the specified data tuple to the specified table
    """
    if not os.path.isfile(config.database_path): return False
    free_space = helpers.remaining_space("/")
    if free_space == None or free_space < 0.1: return False

    if table == DbTable.REPORTS:
        query = ("INSERT INTO reports VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, "
            + "?, ?, ?, ?)")
    elif table == DbTable.ENVREPORTS:
        query = "INSERT INTO envReports VALUES (?, ?, ?)"
    elif table == DbTable.DAYSTATS:
        query = ("INSERT INTO dayStats (Date, AirT_Avg, AirT_Min, AirT_Max, "
            + "RelH_Avg, RelH_Min, RelH_Max, DewP_Avg, DewP_Min, DewP_Max, "
            + "WSpd_Avg, WSpd_Min, WSpd_Max, WDir_Avg, WDir_Min, WDir_Max, "
            + "WGst_Avg, WGst_Min, WGst_Max, SunD_Ttl, Rain_Ttl, MSLP_Avg, "
            + "MSLP_Min, MSLP_Max, ST10_Avg, ST10_Min, ST10_Max, ST30_Avg, "
            + "ST30_Min, ST30_Max, ST00_Avg, ST00_Min, ST00_Max) VALUES (?, ?, "
            + "?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, "
            + "?, ?, ?, ?, ?, ?, ?, ?, ?, ?)")
        
    try:
        with sqlite3.connect(config.database_path) as database:
            cursor = database.cursor()
            cursor.execute(query, data)
            database.commit()
    except: return False
    return True

def update_statistics(data):
    """ Updates the specified dayStats record with the specified data
    """
    if not os.path.isfile(config.database_path): return False
    free_space = helpers.remaining_space("/")
    if free_space == None or free_space < 0.1: return False
        
    try:
        with sqlite3.connect(config.database_path) as database:
            cursor = database.cursor()
            cursor.execute("UPDATE dayStats SET AirT_Avg = ?, AirT_Min = ?, "
                + "AirT_Max = ?, RelH_Avg = ?, RelH_Min = ?, RelH_Max = ?, "
                + "DewP_Avg = ?, DewP_Min = ?, DewP_Max = ?, WSpd_Avg = ?, "
                + "WSpd_Min = ?, WSpd_Max = ?, WDir_Avg = ?, WDir_Min = ?, "
                + "WDir_Max = ?, WGst_Avg = ?, WGst_Min = ?, WGst_Max = ?, "
                + "SunD_Ttl = ?, Rain_Ttl = ?, MSLP_Avg = ?, MSLP_Min = ?, "
                + "MSLP_Max = ?, ST10_Avg = ?, ST10_Min = ?, ST10_Max = ?, "
                + "ST30_Avg = ?, ST30_Min = ?, ST30_Max = ?, ST00_Avg = ?, "
                + "ST00_Min = ?, ST00_Max = ? WHERE Date = ?", data)
            database.commit()
    except: return False
    return True

def generate_write_stats(utc):
    """ Calculates and writes/updates statistics for the specified local day to
        the database
    """
    new_stats = calculate_statistics(utc)
    if new_stats == False or new_stats == None:
        helpers.data_error(32)
        return

    local_time = helpers.utc_to_local(utc)

    # Get current stats to decide whether to update existing or insert
    cur_stats = read_record(DbTable.DAYSTATS, local_time)
    if cur_stats == False:
        helpers.data_error(33)
        return

    if cur_stats == None:
        write = write_record(DbTable.DAYSTATS,
            (local_time.strftime("%Y-%m-%d"),
             new_stats["AirT_Avg"], new_stats["AirT_Min"],
             new_stats["AirT_Max"], new_stats["RelH_Avg"],
             new_stats["RelH_Min"], new_stats["RelH_Max"],
             new_stats["DewP_Avg"], new_stats["DewP_Min"],
             new_stats["DewP_Max"], new_stats["WSpd_Avg"],
             new_stats["WSpd_Min"], new_stats["WSpd_Max"],
             new_stats["WDir_Avg"], new_stats["WDir_Min"],
             new_stats["WDir_Max"], new_stats["WGst_Avg"],
             new_stats["WGst_Min"], new_stats["WGst_Max"],
             new_stats["SunD_Ttl"], new_stats["Rain_Ttl"],
             new_stats["MSLP_Avg"], new_stats["MSLP_Min"],
             new_stats["MSLP_Max"], new_stats["ST10_Avg"],
             new_stats["ST10_Min"], new_stats["ST10_Max"],
             new_stats["ST30_Avg"], new_stats["ST30_Min"],
             new_stats["ST30_Max"], new_stats["ST00_Avg"],
             new_stats["ST00_Min"], new_stats["ST00_Max"]))
        if write == False: helpers.data_error(34)

    else:
        write = update_statistics((new_stats["AirT_Avg"],
             new_stats["AirT_Min"], new_stats["AirT_Max"],
             new_stats["RelH_Avg"], new_stats["RelH_Min"],
             new_stats["RelH_Max"], new_stats["DewP_Avg"],
             new_stats["DewP_Min"], new_stats["DewP_Max"],
             new_stats["WSpd_Avg"], new_stats["WSpd_Min"],
             new_stats["WSpd_Max"], new_stats["WDir_Avg"],
             new_stats["WDir_Min"], new_stats["WDir_Max"],
             new_stats["WGst_Avg"], new_stats["WGst_Min"],
             new_stats["WGst_Max"], new_stats["SunD_Ttl"],
             new_stats["Rain_Ttl"], new_stats["MSLP_Avg"],
             new_stats["MSLP_Min"], new_stats["MSLP_Max"],
             new_stats["ST10_Avg"], new_stats["ST10_Min"],
             new_stats["ST10_Max"], new_stats["ST30_Avg"],
             new_stats["ST30_Min"], new_stats["ST30_Max"],
             new_stats["ST00_Avg"], new_stats["ST00_Min"],
             new_stats["ST00_Max"], local_time.strftime("%Y-%m-%d")))
        if write == False: helpers.data_error(35)

def calculate_statistics(utc):
    """ Calculate reports table statistics for the day in the local time zone
        corresponding to the specified utc time
    """
    bounds = helpers.day_bounds_utc(helpers.utc_to_local(utc), False)

    try:
        with sqlite3.connect(config.database_path) as database:
            database.row_factory = sqlite3.Row
            cursor = database.cursor()

            # Generate the statistics
            one_min = timedelta(minutes=1)
            cursor.execute("SELECT * FROM (SELECT ROUND(AVG(ST10), 3) AS "
                + "ST10_Avg, MIN(ST10) AS ST10_Min, MAX(ST10) AS ST10_Max, "
                + "ROUND(AVG(ST30), 3) AS ST30_Avg, MIN(ST30) AS ST30_Min, MAX("
                + "ST30) AS ST30_Max, ROUND(AVG(ST00), 3) AS ST00_Avg, MIN("
                + "ST00) AS ST00_Min, MAX(ST00) AS ST00_Max FROM reports WHERE "
                + "Time BETWEEN ? AND ?) AS A INNER JOIN (SELECT ROUND(AVG(AirT"
                + "), 3) AS AirT_Avg, MIN(AirT) AS AirT_Min, MAX(AirT) AS "
                + "AirT_Max, ROUND(AVG(RelH), 3) AS RelH_Avg, MIN(RelH) AS "
                + "RelH_Min, MAX(RelH) AS RelH_Max, ROUND(AVG(DewP), 3) AS "
                + "DewP_Avg, MIN(DewP) AS DewP_Min, MAX(DewP) AS DewP_Max, "
                + "ROUND(AVG(WSpd), 3) AS WSpd_Avg, MIN(WSpd) AS WSpd_Min, MAX("
                + "WSpd) AS WSpd_Max, ROUND(AVG(WDir), 3) AS WDir_Avg, MIN(WDir"
                + ") AS WDir_Min, MAX(WDir) AS WDir_Max, ROUND(AVG(WGst), 3) AS"
                + " WGst_Avg, MIN(WGst) AS WGst_Min, MAX(WGst) AS WGst_Max, "
                + "SUM(SunD) AS SunD_Ttl, ROUND(SUM(Rain), 3) AS Rain_Ttl, "
                + "ROUND(AVG(MSLP), 3) AS MSLP_Avg, MIN(MSLP) AS MSLP_Min, MAX("
                + "MSLP) AS MSLP_Max FROM reports WHERE Time BETWEEN ? AND ?) "
                + "AS B", (bounds[0].strftime("%Y-%m-%d %H:%M:%S"),
                           bounds[1].strftime("%Y-%m-%d %H:%M:%S"),
                           (bounds[0] + one_min).strftime("%Y-%m-%d %H:%M:%S"),
                           (bounds[1] + one_min).strftime("%Y-%m-%d %H:%M:%S")))
                            
            return cursor.fetchone()
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