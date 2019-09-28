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

# Illuminate LEDs to indicate startup has begun
if config.data_led_pin != None:
    gpio.setup(config.data_led_pin, gpio.OUT)
    gpio.output(config.data_led_pin, gpio.HIGH)

if config.error_led_pin != None:
    gpio.setup(config.error_led_pin, gpio.OUT)
    gpio.output(config.error_led_pin, gpio.HIGH)

if config.power_led_pin != None:
    gpio.setup(config.power_led_pin, gpio.OUT)
    gpio.output(config.power_led_pin, gpio.HIGH)

time.sleep(2.5)
if config.data_led_pin != None:
    gpio.output(config.data_led_pin, gpio.LOW)
if config.error_led_pin != None:
    gpio.output(config.error_led_pin, gpio.LOW)
if config.power_led_pin != None:
    gpio.output(config.power_led_pin, gpio.LOW)
time.sleep(0.5)


# Main filesystem initialisation checks
free_space = helpers.remaining_space(config.data_directory)

if free_space != None and free_space >= 0.1:
    try:
        if not os.path.isdir(config.data_directory):
            os.makedirs(config.data_directory)
    except: helpers.init_error(2, False, True)

    helpers.write_log("init",
        "Configuration valid. Remaining data drive space: "
        + str(round(free_space, 2)) + " GB")

    # Create main database
    try:
        if not os.path.isfile(config.main_db_path):
            data.create_database(config.main_db_path)
    except: helpers.init_error(3, True, True)

    # Create upload database
    if (config.report_uploading == True or
        config.envReport_uploading == True or
        config.camera_uploading == True or
        config.dayStat_uploading == True):

        try:
            if not os.path.isfile(config.upload_db_path):
                data.create_database(config.upload_db_path)
        except: helpers.init_error(4, True, True)
else: helpers.init_error(1, False, True)


# Check camera storage drive is ready for use
if config.camera_logging == True:
    try:
        if not os.path.isdir(config.camera_directory):
            raise Exception("Directory does not exist")
    except: helpers.init_error(5, True, True)

    try:
        if not os.path.ismount(config.camera_directory):
            raise Exception("Directory not a mount point")
    except: helpers.init_error(6, True, True)

    free_space = helpers.remaining_space(config.camera_directory)
    if free_space == None or free_space < 0.1:
        helpers.init_error(7, True, True)


# Start data and support subsystems
if config.data_led_pin != None:
    gpio.output(config.data_led_pin, gpio.HIGH)
if config.error_led_pin != None:
    gpio.output(config.error_led_pin, gpio.HIGH)
if config.power_led_pin != None:
    gpio.output(config.power_led_pin, gpio.HIGH)

try:
    with open(os.devnull, "w") as devnull:
        subprocess.Popen(["python3", "aws_data.py"], stdout=devnull,
            stderr=devnull)
except: helpers.init_error(8, True, False)

try:
    with open(os.devnull, "w") as devnull:
        subprocess.Popen(["python3", "aws_support.py"], stdout=devnull,
            stderr=devnull)
except: helpers.init_error(9, True, False)