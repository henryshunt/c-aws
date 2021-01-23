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

        QUERY = ("CREATE TABLE dayStats (Date TEXT PRIMARY KEY NOT NULL, "
            + "{0}AirT_Avg REAL, AirT_Min REAL, AirT_Max REAL, RelH_Avg REAL, "
            + "RelH_Min REAL, RelH_Max REAL, DewP_Avg REAL, DewP_Min REAL, "
            + "DewP_Max REAL, WSpd_Avg REAL, WSpd_Min REAL, WSpd_Max REAL, "
            + "WDir_Avg INTEGER, WGst_Avg REAL, WGst_Min REAL, WGst_Max REAL, "
            + "SunD_Ttl INTEGER, Rain_Ttl REAL, MSLP_Avg REAL, MSLP_Min REAL, "
            + "MSLP_Max REAL, ST10_Avg REAL, ST10_Min REAL, ST10_Max REAL, "
            + "ST30_Avg REAL, ST30_Min REAL, ST30_Max REAL, ST00_Avg REAL, "
            + "ST00_Min REAL, ST00_Max REAL)")

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
    try:
        if not os.path.isfile(db_path): return False
    except: return False

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

def write_report(report):
    QUERY = ("INSERT INTO reports VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, "
            + "?, ?, ?, ?)")

    values = (report.time.strftime("%Y-%m-%d %H:%M:%S"), report.air_temp,
        None, report.rel_hum, report.dew_point,
        report.wind_speed, report.wind_dir, report.wind_gust, 
        report.sun_dur, report.rainfall, report.sta_pres,
        report.msl_pres, None, None, None)

    query = query_database(config.main_db_path, QUERY, values)
    
    if query == True:
        if config.report_uploading == True:
            query = query_database(config.upload_db_path, QUERY, values)

            if query == False:
                helpers.log(None, "coord", "operation_log_report() 5")
    else: helpers.log(None, "coord", "operation_log_report() 4")

def dew_point(AirT, RelH):
    """ Calculates dew point using the same formula the Met Office uses
    """
    if AirT == None or RelH == None: return None

    ea = (8.082 - AirT / 556.0) * AirT
    e = 0.4343 * math.log(RelH / 100) + ea / (256.1 + AirT)
    sr = math.sqrt(((8.0813 - e) ** 2) - (1.842 * e))
    return 278.04 * ((8.0813 - e) - sr)

def mslp(StaP, AirT):
    """ Reduces station pressure to mean sea level using the formula at
        https://keisan.casio.com/exec/system/1224575267
    """
    if StaP == None or AirT == None: return None

    a = ((0.0065 * config.aws_elevation)
        / (AirT + (0.0065 * config.aws_elevation) + 273.15))
    return StaP * ((1 - a) ** -5.257)


class Report():
    def __init__(self, time):
        self.time = time
        self.air_temp = None
        self.rel_hum = None
        self.dew_point = None
        self.wind_speed = None
        self.wind_dir = None
        self.wind_gust = None
        self.sun_dur = None
        self.rainfall = None
        self.sta_pres = None
        self.msl_pres = None