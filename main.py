import os
import time
import sqlite3
import subprocess

import RPi.GPIO as gpio

import routines.config as config
import routines.helpers as helpers
import routines.queries as queries

proc_support = None
proc_data = None

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
    if not os.path.isdir(config.camera_directory): helpers.init_error(5)
    if not os.path.ismount(config.camera_directory): helpers.init_error(6)

    free_space = helpers.remaining_space(config.camera_directory)
    if free_space == None or free_space < 5: helpers.init_error(7)


# -- RUN SUPPORT SUBSYSTEM ----------------------------------------------------
try:
    proc_support = subprocess.Popen(["python3", "aws_support.py"])
except: helpers.init_error(8)

# -- RUN DATA SUBSYSTEM -------------------------------------------------------
try:
    proc_data = subprocess.Popen(["python3", "aws_data.py"])
    gpio.output(helpers.DATALEDPIN, gpio.HIGH)
    gpio.output(helpers.ERRORLEDPIN, gpio.HIGH)
    
except:
    proc_support.terminate()
    helpers.init_error(9)