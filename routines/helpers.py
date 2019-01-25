import sys
import os
from datetime import datetime, timedelta
import time
import math

import RPi.GPIO as gpio
import pytz

# Constants indicating pin numbers of the data and error LEDs
DATALEDPIN = 23
ERRORLEDPIN = 24

def init_exit(code):
    """ Remains in a loop, flashing the error LED to indicate an error code
    """
    while True:
        for i in range(code):
            gpio.output(ERRORLEDPIN, gpio.HIGH)
            time.sleep(0.15)
            gpio.output(ERRORLEDPIN, gpio.LOW)
            time.sleep(0.15)

        time.sleep(1)

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

def utc_to_local(config, utc):
    """ Localises a UTC time to the time zone specified in the configuration
    """
    localised = pytz.utc.localize(utc.replace(tzinfo = None))
    return localised.astimezone(config.aws_time_zone).replace(tzinfo = None)

def local_to_utc(config, local):
    """ Converts a localised time to UTC, based on the time zone in the config
    """
    localised = config.aws_time_zone.localize(local.replace(tzinfo = None))
    return localised.astimezone(pytz.utc).replace(tzinfo = None)

def day_bounds_utc(config, local, inclusive):
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
    return local_to_utc(config, start), local_to_utc(config, end)

def calculate_dew_point(AirT, RelH):
    DewP_a = 0.4343 * math.log(RelH / 100)
    DewP_b = ((8.082 - AirT / 556.0) * AirT)
    DewP_c = DewP_a + (DewP_b) / (256.1 + AirT)
    DewP_d = math.sqrt((8.0813 - DewP_c) ** 2 - (1.842 * DewP_c))

    return 278.04 * ((8.0813 - DewP_c) - DewP_d)

def calculate_mean_sea_level_pressure(config, StaP, AirT, DewP):
    MSLP_a = 6.11 * 10 ** ((7.5 * DewP) / (237.3 + DewP))
    MSLP_b = (9.80665 / 287.3) * config.aws_elevation
    MSLP_c = ((0.0065 * config.aws_elevation) / 2) 
    MSLP_d = AirT + 273.15 + MSLP_c + MSLP_a * 0.12
    
    return StaP * math.exp(MSLP_b / MSLP_d)