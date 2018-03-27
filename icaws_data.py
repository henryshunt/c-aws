""" ICAWS Data Acquisition Program
      Responsible for measuring and logging data parameters, and for generating
      statistics. This is the entry point for the ICAWS software
"""

import sys
import subprocess
import os
from datetime import datetime, timedelta
import time
import picamera
import RPi.GPIO as gpio

import sqlite3
from apscheduler.schedulers.blocking import BlockingScheduler

from config import ConfigData
import helpers


print("          ICAWS Data Acquisition Software, Version 4 - 2018, Henry Hunt"
    + "\n*********************************************************************"
    + "***********\n\n                          DO NOT TERMINATE THIS PROGRAM")
time.sleep(2.5)


config = ConfigData()
data_start_time = None


def every_minute():
    """ Triggered every minute to generate a report, add it to the database,
        activate the camera and generate statistics
    """
    time.sleep(0.1)
    pass

def every_second():
    """ Triggered every second to read sensor values into a list for averaging
    """
    pass


if __name__ == "__main__":
    try:
        gpio.setwarnings(False)

        # Initialise GPIO and LED for software error indication
        gpio.setmode(gpio.BCM)
        gpio.setup(11, gpio.OUT)
        gpio.setup(12, gpio.out)
    except: helpers.exit_without_indicator("00")


    free_space = helpers.remaining_space("/")
    if free_space == None or free_space < 1: helpers.exit("00")

    config_load = config.load()
    if config_load == None: helpers.exit("01")

    # Check data directory and create if doesn't exist
    if config.data_directory == None: helpers.exit("02")
    if not os.path.isdir(config.data_directory):
        try:
            os.makedirs(comfig.data_directory)
        except: helpers.exit("03")

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
        except: helpers.exit("04")

    # Check camera drive if configuration modifier is active
    if config.camera_logging == True:
        if config.camera_drive == None: helpers.exit("05")
        if not os.path.isdir(config.camera_drive): helpers.exit("06")

        free_space = helpers.remaining_space(config.camera_drive)
        if free_space == None or free_space < 5: helpers.exit("07")

        # Check camera is connected to system
        # TODO: #1 exit code 08
        try:
            with picamera.PiCamera() as camera: pass
        except: helpers.exit("08")
    
    # Check backup drive if configuration modifier is active
    if config.backups == True:
        if config.backup_drive == None: helpers.exit("09")
        if not os.path.isdir(config.backup_drive): helpers.exit("10")

        free_space = helpers.remaining_space(config.backup_drive)
        if free_space == None or free_space < 5: helpers.exit("11")

    # Check graph directory if configuration modifier is active
    if (config.day_graph_generation == True or
        config.month_graph_generation == True or
        config.year_graph_generation == True):

        if not os.path.isdir(config.graph_directory):
            try:
                os.makedirs(config.graph_directory)
            except: helpers.exit("12")

    # Check endpoints if configuration modifiers are active
    if (config.report_uploading == True or
        config.statistic_uploading == True):

        if config.remote_sql_server == None: helpers.exit("13")

    if (config.camera_uploading == True or
        config.day_graph_uploading == True or
        config.month_graph_uploading == True or
        config.year_graph_uploading == True):

        if (config.remote_ftp_server == None or
            config.remote_ftp_username == None or
            config.remote_ftp_password == None):

            helpers.exit("14")


    # Start data support and data access subprocesses
    current_dir = os.path.dirname(os.path.realpath(__file__))

    if (config.day_graph_generation == True or
        config.month_graph_generation == True or
        config.year_graph_generation == True or
        config.report_uploading == True or
        config.statistic_uploading == True or
        config.camera_uploading == True or
        config.day_graph_uploading == True or
        config.month_graph_uploading == True or
        config.year_graph_uploading == True or
        config.integrity_checks == True or
        config.backups == True):

        subprocess.Popen(["lxterminal -e python3 "
                          + current_dir + "icaws_support.py"], shell = True)
    
    if config.local_network_server == True:
        subprocess.Popen(["lxterminal -e python3 "
                          + current_dir + "icaws_access.py"], shell = True)

    # Wait for next minute to begin to ensure proper averaging
    while True:
        if datetime.now().second != 0:
            time.sleep(0.1)
        else: break

    # Initialise GPIOs, start data logging and record start time
    data_start_time = datetime.now().replace(second = 0, microsecond = 0)

    event_scheduler = BlockingScheduler()
    event_scheduler.add_job(every_minute, "cron", minute = "0-59")
    event_scheduler.add_job(every_second, "cron", second = "0-59")
    event_scheduler.start()

    print("active")
