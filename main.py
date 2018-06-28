""" C-AWS Main Entry Point
      Performs initial environment checks and then starts the three sub-systems
"""

# DEPENDENCIES -----------------------------------------------------------------
import os
from datetime import datetime
import RPi.GPIO as gpio
import time
import sqlite3
import picamera
import subprocess

from config import ConfigData
import helpers
import queries

# MESSAGE ----------------------------------------------------------------------
print("--- Custom Automatic Weather Station ---")
print("Program: C-AWS Main Entry Point")
print("Author:  Henry Hunt")
print("Version: V4.B0 (June 2018)")
print("")
print("----------- DO NOT TERMINATE -----------")

# GLOBAL VARIABLES -------------------------------------------------------------
config = ConfigData()
software_start = None


# ENTRY POINT ==================================================================
# -- INIT GPIO AND LEDS --------------------------------------------------------
software_start = datetime.utcnow()

try:
    gpio.setwarnings(False); gpio.setmode(gpio.BCM)
    gpio.setup(23, gpio.OUT); gpio.output(23, gpio.LOW)
    gpio.setup(24, gpio.OUT); gpio.output(24, gpio.LOW)
except: helpers.exit_no_light("00")

time.sleep(2.5)

# -- CHECK INTERNAL DRIVE ------------------------------------------------------
free_space = helpers.remaining_space("/")
if free_space == None or free_space < 1: helpers.exit("01")

# -- CHECK CONFIG --------------------------------------------------------------
if config.load() == False: helpers.exit("02")
if config.validate() == False: helpers.exit("03")

# -- CHECK DATA DIRECTORY ------------------------------------------------------
if not os.path.isdir(config.data_directory):
    try:
        os.makedirs(config.data_directory)
    except: helpers.exit("04")

# -- MAKE DATABASE -------------------------------------------------------------
if not os.path.isfile(config.database_path):
    try:
        with sqlite3.connect(config.database_path) as database:
            cursor = database.cursor()

            cursor.execute(queries.CREATE_UTCREPORTS_TABLE)
            cursor.execute(queries.CREATE_UTCENVIRON_TABLE)
            cursor.execute(queries.CREATE_LOCALSTATS_TABLE)
            database.commit()

    except: helpers.exit("05")

# -- CHECK CAMERA DRIVE --------------------------------------------------------
if config.camera_logging == True:
    if not os.path.isdir(config.camera_drive): helpers.exit("06")

    free_space = helpers.remaining_space(config.camera_drive)
    if free_space == None or free_space < 5: helpers.exit("07")

    # Check camera module is connected
    try:
        with picamera.PiCamera() as camera: pass
    except: helpers.exit("08")

# -- CHECK BACKUP DRVIE --------------------------------------------------------
if config.backups == True:
    if not os.path.isdir(config.backup_drive): helpers.exit("09")

    free_space = helpers.remaining_space(config.backup_drive)
    if free_space == None or free_space < 5: helpers.exit("10")

# -- RUN SUBPROCESSES ----------------------------------------------------------
current_dir = os.path.dirname(os.path.realpath(__file__))

try:
    subprocess.Popen(["lxterminal -e python3 " + current_dir
                      + "/aws_data.py"], shell = True)
except: helpers.exit("11")

if (config.report_uploading == True or
    config.environment_uploading == True or
    config.statistic_uploading == True or
    config.camera_uploading == True or
    config.integrity_checks == True or
    config.backups == True):

    try:
        subprocess.Popen(["lxterminal -e python3 " + current_dir
                          + "/aws_support.py"], shell = True)
    except: helpers.exit("12")

if config.local_network_server == True:
    try:
        time_arg = software_start.strftime("%Y-%m-%dT%H:%M:%S")
        subprocess.Popen(["lxterminal -e python3 " + current_dir
                          + "/aws_access.py " + time_arg], shell = True)
    except: helpers.exit("13")