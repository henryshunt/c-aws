""" C-AWS Main Entry Point
      Performs initialisation, system checks, and starts the sub-systems
"""

# DEPENDENCIES -----------------------------------------------------------------
import os
from datetime import datetime
import time
import sqlite3
import subprocess

import RPi.GPIO as gpio
import picamera

import routines.config as config
import routines.helpers as helpers
import routines.queries as queries

# GLOBAL VARIABLES -------------------------------------------------------------
startup_time = datetime.utcnow()

proc_data = None
proc_support = None
proc_access = None

# -- INIT GPIO AND LEDS --------------------------------------------------------
gpio.setwarnings(False)
gpio.setmode(gpio.BCM)

# Setup and reset the data and error LEDs
gpio.setup(helpers.DATALEDPIN, gpio.OUT)
gpio.output(helpers.DATALEDPIN, gpio.LOW)
gpio.setup(helpers.ERRORLEDPIN, gpio.OUT)
gpio.output(helpers.ERRORLEDPIN, gpio.LOW)

# Illuminate both LEDs for 2.5 seconds to indicate startup
gpio.output(helpers.DATALEDPIN, gpio.HIGH)
gpio.output(helpers.ERRORLEDPIN, gpio.HIGH)
time.sleep(2.5)
gpio.output(helpers.DATALEDPIN, gpio.LOW)
gpio.output(helpers.ERRORLEDPIN, gpio.LOW)

# -- CHECK CONFIG --------------------------------------------------------------
if config.load() == False: helpers.init_error(1)

# -- CHECK INTERNAL DRIVE ------------------------------------------------------
free_space = helpers.remaining_space("/")
if free_space == None or free_space < 1: helpers.init_error(2)

# -- CHECK DATA DIRECTORY ------------------------------------------------------
if not os.path.isdir(config.data_directory):
    try:
        os.makedirs(config.data_directory)
    except: helpers.init_error(3)

# -- MAKE DATABASE -------------------------------------------------------------
if not os.path.isfile(config.database_path):
    try:
        with sqlite3.connect(config.database_path) as database:
            cursor = database.cursor()
            cursor.execute(queries.CREATE_REPORTS_TABLE)
            cursor.execute(queries.CREATE_ENVREPORTS_TABLE)
            cursor.execute(queries.CREATE_DAYSTATS_TABLE)

            database.commit()
    except: helpers.init_error(4)

# -- CHECK CAMERA DRIVE --------------------------------------------------------
if config.camera_logging == True:
    try:
        blocks = subprocess.Popen(["sudo", "blkid"],
            stdout = subprocess.PIPE, stderr = subprocess.DEVNULL)
        blocks.wait()

        # Check if specified camera drive is not connected
        if config.camera_drive_label not in str(blocks.stdout.read()):
            helpers.init_error(5)
    
        if not os.path.exists(config.camera_drive):
            os.makedirs(config.camera_drive)

        # Mount the specified drive via its label
        mount = subprocess.Popen(["sudo", "mount", "-L",
            config.camera_drive_label, config.camera_drive],
            stdout = subprocess.DEVNULL, stderr = subprocess.DEVNULL)
        mount.wait()
    except: helpers.init_error(6)

    free_space = helpers.remaining_space(config.camera_drive)
    if free_space == None or free_space < 5: helpers.init_error(7)

    # Check camera module is connected
    try:
        with picamera.PiCamera() as camera: pass
    except: helpers.init_error(8)


# -- RUN ACCESS SUBSYSTEM -----------------------------------------------------
try:
    proc_access = subprocess.Popen(["sudo", "python3", "aws_access.py",
        startup_time.strftime("%Y-%m-%dT%H:%M:%S")])
except: helpers.init_error(9)

# -- RUN SUPPORT SUBSYSTEM ----------------------------------------------------
if (config.report_uploading == True or
    config.envReport_uploading == True or
    config.dayStat_uploading == True or
    config.camera_uploading == True):

    try:
        proc_support = subprocess.Popen(["sudo", "python3", "aws_support.py"])

    except:
        if proc_access != None: proc_access.terminate()
        helpers.init_error(10)

# -- RUN DATA SUBSYSTEM -------------------------------------------------------
try:
    proc_data = subprocess.Popen(["sudo", "python3", "aws_data.py"])
    gpio.output(helpers.DATALEDPIN, gpio.HIGH)
    gpio.output(helpers.ERRORLEDPIN, gpio.HIGH)
    
except:
    if proc_access != None: proc_access.terminate()
    if proc_support != None: proc_support.terminate()
    helpers.init_error(11)