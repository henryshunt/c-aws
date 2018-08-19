import sys
import os
from datetime import datetime, timedelta
import time

import RPi.GPIO as gpio
import pytz

def init_exit(code, visual):
    if visual == True:
        while True:
            for i in range(code):
                gpio.output(24, gpio.HIGH); time.sleep(0.15)
                gpio.output(24, gpio.LOW); time.sleep(0.15)

            time.sleep(1)
    else: sys.exit(1)

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

def utc_to_local(config, utc):
    localised = pytz.utc.localize(utc.replace(tzinfo = None))
    return localised.astimezone(config.aws_time_zone).replace(tzinfo = None)

def local_to_utc(config, local):
    localised = config.aws_time_zone.localize(local.replace(tzinfo = None))
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