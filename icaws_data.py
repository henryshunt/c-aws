# ICAWS Data Acquisition Program
#  responsible for measuring and logging data parameters, and for generating
#  statistics. This is the entry point for the ICAWS software

import sys
import os

import sqlite3

from config import ConfigData
import helpers


print("          ICAWS Data Acquisition Software, Version 4 - 2018, Henry Hunt         ")
print("********************************************************************************\n")
print("                          DO NOT TERMINATE THIS PROGRAM                         ")


config = ConfigData()


if __name__ == "__main__":
    rem_space = helpers.remaining_space("/")
    print(rem_space)
    if rem_space == None or rem_space < 500: sys.exit(1)

    # Cannot start ICAWS software without a configuration profile
    config_load = config.load()
    
    if config_load == False: sys.exit(1)
    if config.database_path == None: sys.exit(1)
    if not os.path.exists(os.path.dirname(config.database_path)): sys.exit(1)

    # Create new database if one doesn't exist
    if not os.path.isfile(config.database_path):
        with sqlite3.connect(config.database_path) as database:
            cursor = database.cursor()
            cursor.execute("CREATE TABLE utcReports (" +
                                "Time TEXT PRIMARY KEY NOT NULL," +
                                "AirT REAL, ExpT REAL, RelH REAL," +
                                "DewP REAL, WSpd REAL, WDir REAL," +
                                "WGst REAL, SunD REAL, Rain REAL," +
                                "StaP REAL, PTen REAL, MSLP REAL," +
                                "ST10 REAL, ST30 REAL, ST00 REAL" +
                            ")")
            cursor.execute("CREATE TABLE utcEnviron (" +
                                "Time TEXT PRIMARY KEY NOT NULL," +
                                "EncT REAL, CPUT REAL" +
                            ")")
            cursor.execute("CREATE TABLE localStats (" +
                                "Date TEXT PRIMARY KEY NOT NULL," +
                                "AirT_Min REAL, AirT_Max REAL," +
                                "AirT_Avg REAL, RelH_Min REAL," +
                                "RelH_Max REAL, RelH_Avg REAL," +
                                "DewP_Min REAL, DewP_Max REAL," +
                                "DewP_Avg REAL, WSpd_Max REAL," +
                                "WSpd_Avg REAL, WDir_Avg REAL," +
                                "WGst_Max REAL, WGst_Avg REAL," +
                                "SunD_Ttl REAL, Rain_Ttl REAL," +
                                "MSLP_Min REAL, MSLP_Max REAL," +
                                "MSLP_Avg REAL, TS10_Min REAL," +
                                "TS10_Max REAL, TS10_Avg REAL," +
                                "TS30_Min REAL, TS30_Max REAL," +
                                "TS30_Avg REAL, TS00_Min REAL," +
                                "TS00_Max REAL, TS00_Avg REAL" +
                            ")")
            database.commit()
