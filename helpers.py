import sys
import os
from datetime import datetime
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
            file.write("initialisation failure at {} with exit code {}"
                       .format(datetime.now()
                               .strftime("%Y-%m-%d %H:%M:%S"), code))

            gpio.output(23, gpio.HIGH)
            sys.exit(1)
            
    except: sys.exit(1)

def exit_no_light(code):
    try:
        with open("init.txt", "w+") as file:
            file.write("initialisation failure at {} with exit code {}"
                       .format(datetime.now()
                               .strftime("%Y-%m-%d %H:%M:%S"), code))
            sys.exit(1)

    except: sys.exit(1)

def init_success():
    try:
        with open("init.txt", "w+") as file:
            file.write("initialisation success at {}"
                       .format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

    except: sys.exit(1)

def utc_to_local(utc, timezone):
    utc_time = pytz.utc.localize(utc)
    return (utc_time.astimezone(pytz.timezone(timezone)).replace(tzinfo = None))