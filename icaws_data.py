""" ICAWS Data Acquisition Program
      Responsible for measuring and logging data parameters, and for generating
      statistics. This is the entry point for the ICAWS software
"""

import sys
import subprocess
import os
from datetime import datetime, timedelta
import time

import sqlite3

from config import ConfigData
import helpers


print("          ICAWS Data Acquisition Software, Version 4 - 2018, Henry Hunt"
    + "\n*********************************************************************"
    + "***********\n\n                          DO NOT TERMINATE THIS PROGRAM")
time.sleep(2.5)


config = ConfigData()
data_start_time = None


if __name__ == "__main__":
    free_space = helpers.remaining_space("/")
    if free_space == None or free_space < 1: sys.exit(1)

    # Cannot start ICAWS software without a configuration profile
    config_load = config.load()
    if config_load == None: sys.exit(1)

    if not os.path.isdir(os.path.dirname(config.database_path)):
        try:
            os.makedirs(os.path.dirname(config.database_path))
        except: sys.exit(1)

    # Create a new database if one doesn't exist already
    if not os.path.isfile(config.database_path):
        try:
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
        except: sys.exit(1)

    # Check camera drive if configuration modifier is active
    if config.camera_logging == True:
        if not os.path.isdir(config.camera_drive): sys.exit(1)

        free_space = helpers.remaining_space(config.camera_drive)
        if free_space == None or free_space < 5: sys.exit(1)

        # Check camera is connected to system
        # TODO: #1
    
    # Check backup drive if configuration modifier is active
    if config.backups == True:
        if not os.path.isdir(config.backup_drive): sys.exit(1)

        free_space = helpers.remaining_space(config.backup_drive)
        if free_space == None or free_space < 5: sys.exit(1)

    # Check graph directory if configuration modifier is active
    if config.day_graph_generation == True or
            config.month_graph_generation == True or
            config.year_graph_generation == True:

        if not os.path.isdir(config.graph_directory):
            try:
                os.makedirs(config.graph_directory)
            except: sys.exit(1)

    # Start data support and data access subprocesses
    current_dir = os.path.dirname(os.path.realpath(__file__))

    if (config.today_graph_generation == True or
            config.month_graph_generation == True or
            config.year_graph_generation == True or
            config.report_uploading == True or
            config.statistic_uploading == True or
            config.camera_uploading == True or
            config.today_graph_uploading == True or
            config.month_graph_uploading == True or
            config.year_graph_uploading == True or
            config.integrity_checks == True or
            config.backups == True):
            
        subprocess.Popen(["lxterminal -e python3 "
            + current_dir + "icaws_support.py"], shell = True)
    
    if config.local_network_server == True:
        subprocess.Popen(["lxterminal -e python3 "
            + current_dir + "icaws_access.py"], shell = True)

    # Wait for next minute to begin to ensure proper average calculations
    while True:
        if datetime.now().second != 0:
            time.sleep(0.1)
        else: break

    # Start data logging and record start time
    data_start_time = datetime.now().replace(second = 0, microsecond = 0)
    print("active")
