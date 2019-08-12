import time
import os
import subprocess

import RPi.GPIO as gpio

import routines.config as config
import routines.helpers as helpers
import routines.data as data


# Set up and reset data and error indicator LEDs
gpio.setwarnings(False)
gpio.setmode(gpio.BCM)

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


# Loading the configuration file
if config.load() == False: helpers.init_error(0)

# Check remaining space on internal computer drive
free_space = helpers.remaining_space("/")
if free_space == None or free_space < 1: helpers.init_error(1)

# Create data directory if it doesn't exist
if not os.path.isdir(config.data_directory):
    try:
        os.makedirs(config.data_directory)
    except: helpers.init_error(2)

# Create database if it doesn't exist
if not os.path.isfile(config.database_path):
    try:
        data.create_database(config.database_path)
    except: helpers.init_error(3)

# Check camera image storage drive is ready for use
if config.camera_logging == True:
    if not os.path.isdir(config.camera_directory): helpers.init_error(4)
    if not os.path.ismount(config.camera_directory): helpers.init_error(5)

    free_space = helpers.remaining_space(config.camera_directory)
    if free_space == None or free_space < 5: helpers.init_error(6)


# Start support subsystem
try:
    with open(os.devnull, "w") as devnull:
        proc_support = subprocess.Popen(["python3", "aws_support.py"],
            stdout=devnull, stderr=devnull)
except: helpers.init_error(7)

# Start data subsystem
try:
    with open(os.devnull, "w") as devnull:
        subprocess.Popen(["python3", "aws_data.py"], stdout=devnull,
            stderr=devnull)

except:
    if proc_support.poll() == None: proc_support.terminate()
    helpers.init_error(8)

gpio.output(helpers.DATALEDPIN, gpio.HIGH)
gpio.output(helpers.ERRORLEDPIN, gpio.HIGH)