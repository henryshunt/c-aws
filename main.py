""" C-AWS Main Entry Point
      Performs the initial environment checks and starts the sub-systems
"""

# DEPENDENCIES -----------------------------------------------------------------
import os
from datetime import datetime
import time
import sqlite3
import subprocess
import hashlib

import RPi.GPIO as gpio
import picamera

from config import ConfigData
import helpers
import queries

# MESSAGE ----------------------------------------------------------------------
print("--- Custom Automatic Weather Station ---")
print("Program: Software Entry Point")
print("Author:  Henry Hunt")
print("Version: 4C.1 (July 2018)")
print("")
print("----------- DO NOT TERMINATE -----------")

# GLOBAL VARIABLES -------------------------------------------------------------
config = ConfigData()
startup_time = datetime.utcnow()

# CLEAR STATE ------------------------------------------------------------------
try:
    if os.path.isfile("__init.txt"): os.remove("__init.txt")
except: print("state clear failure")

# -- INIT GPIO AND LEDS --------------------------------------------------------
try:
    gpio.setwarnings(False); gpio.setmode(gpio.BCM)
    gpio.setup(23, gpio.OUT); gpio.output(23, gpio.LOW)
    gpio.setup(24, gpio.OUT); gpio.output(24, gpio.LOW)
except: helpers.init_exit("00", False)

gpio.output(23, gpio.HIGH); gpio.output(24, gpio.HIGH)
time.sleep(2.5)
gpio.output(23, gpio.LOW); gpio.output(24, gpio.LOW)

# -- CHECK CONFIG --------------------------------------------------------------
if config.load() == False: helpers.init_exit("01", True)
if config.validate() == False: helpers.init_exit("02", True)

try:
    config_hasher = hashlib.md5()
    with open("__config.ini", "rb") as file: config_hasher.update(file.read())
    config_hash = config_hasher.hexdigest()
    print(config_hash)
except: helpers.init_exit("03", True)

# -- CHECK INTERNAL DRIVE ------------------------------------------------------
free_space = helpers.remaining_space("/")
if free_space == None or free_space < 1: helpers.init_exit("04", True)

# -- CHECK DATA DIRECTORY ------------------------------------------------------
if not os.path.isdir(config.data_directory):
    try:
        os.makedirs(config.data_directory)
    except: helpers.init_exit("05", True)

# -- MAKE DATABASE -------------------------------------------------------------
if not os.path.isfile(config.database_path):
    try:
        with sqlite3.connect(config.database_path) as database:
            cursor = database.cursor()
            cursor.execute(queries.CREATE_REPORTS_TABLE)
            cursor.execute(queries.CREATE_ENVREPORTS_TABLE)
            cursor.execute(queries.CREATE_DAYSTATS_TABLE)

            database.commit()
    except: helpers.init_exit("06", True)

# -- CHECK CAMERA DRIVE --------------------------------------------------------
if config.camera_logging == True:
    if not os.path.isdir(config.camera_drive): helpers.init_exit("07", True)

    free_space = helpers.remaining_space(config.camera_drive)
    if free_space == None or free_space < 5: helpers.init_exit("08", True)

    # Check camera module is connected
    try:
        with picamera.PiCamera() as camera: pass
    except: helpers.init_exit("09", True)

# -- RUN SUBPROCESSES ----------------------------------------------------------
try:
    if config.local_network_server == True:
        subprocess.Popen(["sudo python3 aws_access.py "
                          + startup_time.strftime("%Y-%m-%dT%H:%M:%S")],
                         shell = True)
except: helpers.init_exit("10", True)

if (config.reports_uploading == True or
    config.envReports_uploading == True or
    config.dayStats_uploading == True or
    config.camera_uploading == True):

    try:
        subprocess.Popen(["sudo python3 aws_support.py"], shell = True)
    except: helpers.init_exit("11", True)

try:
    subprocess.Popen(["sudo python3 aws_data.py"], shell = True)
except: helpers.init_exit("12", True)