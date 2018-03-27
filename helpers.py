import sys
import os
from datetime import datetime
import RPi.GPIO as gpio

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
        with open("exit.txt", "w+") as file:
            file.write("initialisation failure at {} with exit code {}"
                       .format(datetime.now()
                               .strftime("%Y-%m-%d %H:%M:%S"), code))

            gpio.output(17, gpio.HIGH)
            sys.exit(1)
            
    except: sys.exit(1)

def exit_without_indicator(code):
    try:
        with open("exit.txt", "w+") as file:
            file.write("initialisation failure at {} with exit code {}"
                       .format(datetime.now()
                               .strftime("%Y-%m-%d %H:%M:%S"), code))
            sys.exit(1)
            
    except: sys.exit(1)
