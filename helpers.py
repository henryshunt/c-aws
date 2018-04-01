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
    return (localised.astimezone(config.icaws_time_zone).replace(tzinfo = None))

def local_to_utc(config, local):
    localised = config.icaws_time_zone.localize(local.replace(tzinfo = None))
    return (localised.astimezone(pytz.utc).replace(tzinfo = None))

# def day_bounds_utc(config, local, inclusive):
#     # Get start and end of local day
#     start = local.replace(hour = 0, minute = 0, second = 0, microsecond = 0)
#     end = local.replace(hour = 23, minute = 59, second = 0, microsecond = 0)

#     # Use start of next day as end if inclusive
#     if inclusive == True: end = local + timedelta(minute = 1)

#     # Convert start and end to utc
#     return local_to_utc(config, start), local_to_utc(config, end)


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
