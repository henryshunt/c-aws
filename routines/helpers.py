import sys
import os
from datetime import datetime, timedelta
import time

import RPi.GPIO as gpio
import pytz

import routines.config as config

# Constants indicating pin numbers of the data and error LEDs
DATALEDPIN = 23
ERRORLEDPIN = 24

def init_error(code):
    """ Remains in a loop, flashing the error LED to indicate an error code
    """
    while True:
        for i in range(code):
            gpio.output(ERRORLEDPIN, gpio.HIGH)
            time.sleep(0.15)
            gpio.output(ERRORLEDPIN, gpio.LOW)
            time.sleep(0.15)

        time.sleep(1)

def data_error(code):
    gpio.output(ERRORLEDPIN, gpio.HIGH)

def remaining_space(directory):
    """ Returns the amount of remaining space in gigabytes, for non-root users,
        for the specified directory to a device
    """
    if not os.path.isdir(directory): return None

    try:
        disk = os.statvfs(directory)

        # Number of blocks * block size, then convert to GB
        non_root_space = float(disk.f_bsize * disk.f_bavail)
        return non_root_space / 1024 / 1024 / 1024
    except: return None

def utc_to_local(utc):
    """ Localises a UTC time to the time zone specified in the configuration
    """
    localised = pytz.utc.localize(utc.replace(tzinfo = None))
    return localised.astimezone(config.aws_time_zone).replace(tzinfo = None)

def local_to_utc(local):
    """ Converts a localised time to UTC, based on the time zone in the config
    """
    localised = config.aws_time_zone.localize(local.replace(tzinfo = None))
    return localised.astimezone(pytz.utc).replace(tzinfo = None)

def day_bounds_utc(local, inclusive):
    """ Calculates the start and end times of the specified local date, in UTC
    """
    # Get start and end of local day
    start = local.replace(
        hour = 0, minute = 0, second = 0, microsecond = 0, tzinfo = None)
    end = local.replace(
        hour = 23, minute = 59, second = 0, microsecond = 0, tzinfo = None)

    # Use start of next day as end if inclusive
    if inclusive == True: end += timedelta(minutes = 1)

    # Convert start and end to UTC
    return local_to_utc(start), local_to_utc(end)