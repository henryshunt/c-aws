import sys
import os
from datetime import datetime, timedelta
import RPi.GPIO as gpio
import pytz

from config import ConfigData

def remaining_space(directory):
    """ Returns the amount of remaining space in gigabytes, for non-root users,
        for the specified directory to a device
    """
    if not os.path.isdir(directory): return None

    try:
        disk = os.statvfs(directory)
        non_root_space = float(disk.f_bsize * disk.f_bavail)
        return non_root_space / 1024 / 1024 / 1024
    except: return None

def exit(code):
    try:
        with open("init.txt", "w+") as file:
            file.write("initialisation failure at {} UTC with exit code {}"
                       .format(datetime.utcnow()
                               .strftime("%Y-%m-%dT%H:%M:%S"), code))
    except: pass

    gpio.output(23, gpio.HIGH)
    sys.exit(1)

def exit_no_light(code):
    try:
        with open("init.txt", "w+") as file:
            file.write("initialisation failure at {} UTC with exit code {}"
                       .format(datetime.utcnow()
                               .strftime("%Y-%m-%dT%H:%M:%S"), code))
    except: pass
    sys.exit(1)

def init_success():
    try:
        with open("init.txt", "w+") as file:
            file.write("initialisation success at {} UTC"
                       .format(datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")))

    except:
        gpio.output(23, gpio.HIGH)
        sys.exit(1)

def utc_to_local(config, utc):
    localised = pytz.utc.localize(utc.replace(tzinfo = None))
    return localised.astimezone(config.caws_time_zone).replace(tzinfo = None)

def local_to_utc(config, local):
    localised = config.caws_time_zone.localize(local.replace(tzinfo = None))
    return localised.astimezone(pytz.utc).replace(tzinfo = None)

def day_bounds_utc(config, local, inclusive):
    # Get start and end of local day
    start = local.replace(hour = 0, minute = 0, second = 0, microsecond = 0,
                          tzinfo = None)
    end = local.replace(hour = 23, minute = 59, second = 0, microsecond = 0,
                        tzinfo = None)

    # Use start of next day as end if inclusive
    if inclusive == True: end += timedelta(minutes = 1)

    # Convert start and end to UTC
    return local_to_utc(config, start), local_to_utc(config, end)

def degrees_to_compass(degrees):
    if degrees >= 338 or degrees < 23: return "N"
    elif degrees >= 23 and degrees < 68: return "NE"
    elif degrees >= 68 and degrees < 113: return "E"
    elif degrees >= 113 and degrees < 158: return "SE"
    elif degrees >= 158 and degrees < 203: return "S"
    elif degrees >= 203 and degrees < 248: return "SW"
    elif degrees >= 248 and degrees < 293: return "W"
    elif degrees >= 293 and degrees < 338: return "NW"

def last_five_mins(utc):
    minute = str(utc.minute)
    
    while not minute.endswith("0") and not minute.endswith("5"):
        utc -= timedelta(minutes = 1)
        minute = str(utc.minute)

    return utc

def none_to_null(value):
    if value == None:
        return "NULL"
    else: return value
