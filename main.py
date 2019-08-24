import time
import os
import subprocess
import sys

import RPi.GPIO as gpio

import routines.config as config
import routines.helpers as helpers
import routines.data as data


# Configuration must be loaded and valid before anything else happens
if config.load() == False: sys.exit(1)


gpio.setwarnings(False)
gpio.setmode(gpio.BCM)

# Set up data and error LEDs and illuminate them
if config.data_led_pin != None:
    gpio.setup(config.data_led_pin, gpio.OUT)
    gpio.output(config.data_led_pin, gpio.HIGH)
if config.error_led_pin != None:
    gpio.setup(config.error_led_pin, gpio.OUT)
    gpio.output(config.error_led_pin, gpio.HIGH)

# Leave LEDs on for 2.5 seconds to indicate startup
time.sleep(2.5)
if config.data_led_pin != None:
    gpio.output(config.data_led_pin, gpio.LOW)
if config.error_led_pin != None:
    gpio.output(config.error_led_pin, gpio.LOW)


# Main filesystem initialisation checks
free_space = helpers.remaining_space(config.data_directory)

if free_space != None and free_space >= 0.1:
    if not os.path.isdir(config.data_directory):
        try:
            os.makedirs(config.data_directory)
        except: helpers.init_error(2, False)

    helpers.write_log("init",
        "Configuration valid. Remaining data drive space: "
        + str(round(free_space, 2)) + " GB")

    # Create main database
    if not os.path.isfile(config.main_db_path):
        try:
            data.create_database(config.main_db_path)
        except: helpers.init_error(3, True)

    # Create upload database
    if (config.report_uploading == True or
        config.envReport_uploading == True or
        config.camera_uploading == True or
        config.dayStat_uploading == True):

        if not os.path.isfile(config.upload_db_path):
            try:
                data.create_database(config.upload_db_path)
            except: helpers.init_error(4, True)
else: helpers.init_error(1, False)


# Check camera storage drive is ready for use
if config.camera_logging == True:
    if not os.path.isdir(config.camera_directory):
        helpers.init_error(5, True)
    if not os.path.ismount(config.camera_directory):
        helpers.init_error(6, True)

    free_space = helpers.remaining_space(config.camera_directory)
    if free_space == None or free_space < 0.1:
        helpers.init_error(7, True)


# Start support subsystem
try:
    with open(os.devnull, "w") as devnull:
        proc_support = subprocess.Popen(["python3", "aws_support.py"],
            stdout=devnull, stderr=devnull)
except: helpers.init_error(8, True)

if config.data_led_pin != None:
    gpio.output(config.data_led_pin, gpio.HIGH)
if config.error_led_pin != None:
    gpio.output(config.error_led_pin, gpio.HIGH)

# Start data subsystem
try:
    with open(os.devnull, "w") as devnull:
        subprocess.Popen(["python3", "aws_data.py"], stdout=devnull,
            stderr=devnull)

except:
    proc_support.terminate()
    helpers.init_error(9, True)