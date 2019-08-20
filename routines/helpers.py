import os
from datetime import datetime, timedelta
import time

import RPi.GPIO as gpio
import pytz
import astral

import routines.config as config


# Constants indicating pin numbers of the data and error LEDs
DATALEDPIN = 23
ERRORLEDPIN = 24


def write_log(source, entry):
    if config.data_directory != None and os.path.isdir(config.data_directory):
        try:
            with open(os.path.join(
                config.data_directory, "log.txt"), "a") as log:
                
                log_time = datetime.utcnow().strftime("%d/%m/%Y %H:%M:%S")
                log.write("[" + log_time + " UTC] -> " + source + " :: " + 
                    str(entry) + "\n")
        except: pass

def init_error(code):
    """ Logs the initialisation error code, then remains in a loop flashing the
        error LED to indicate the error code
    """
    write_log("init", code)
        
    while True:
        for i in range(code):
            gpio.output(ERRORLEDPIN, gpio.HIGH)
            time.sleep(0.15)
            gpio.output(ERRORLEDPIN, gpio.LOW)
            time.sleep(0.15)
        time.sleep(1)

def data_error(entry):
    """ Logs the data subsystem error code and turns on the error LED
    """
    write_log("data", entry)
    gpio.output(ERRORLEDPIN, gpio.HIGH)

def support_error(entry):
    """ Logs the support subsystem error code
    """
    write_log("supp", entry)


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
    localised = pytz.utc.localize(utc.replace(tzinfo=None))
    return localised.astimezone(config.aws_time_zone).replace(tzinfo=None)

def local_to_utc(local):
    """ Converts a localised time to UTC, based on the time zone in the config
    """
    localised = config.aws_time_zone.localize(local.replace(tzinfo=None))
    return localised.astimezone(pytz.utc).replace(tzinfo=None)

def day_bounds_utc(local, inclusive):
    """ Calculates the start and end times of the specified local date, in UTC
    """
    # Get start and end of local day
    start = local.replace(hour=0, minute=0, second=0, microsecond=0,
        tzinfo=None)
    end = local.replace(hour=23, minute=59, second=0, microsecond=0,
        tzinfo=None)

    # Use start of next day as end if inclusive
    if inclusive == True: end += timedelta(minutes=1)
    return local_to_utc(start), local_to_utc(end)

def solar_times(local):
    local = local.replace(hour=12, minute=0)
    
    location = astral.Location(("", "", config.aws_latitude,
        config.aws_longitude, str(config.aws_time_zone), config.aws_elevation))
    solar = location.sun(date=local, local=False)

    return (solar["sunrise"].replace(tzinfo=None),
        solar["sunset"].replace(tzinfo=None))

    
def none_to_null(value):
    """ Returns None if the specified value is null, else returns the value
    """
    return "null" if value == None else value