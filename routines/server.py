import os
from datetime import datetime
import time
import subprocess
import sys

import routines.config as config
import routines.helpers as helpers

def get_static_info():
    startup_time = None
    internal_drive_space = None
    camera_drive_space = None

    # Get system startup time
    try:
        startup_time = subprocess.check_output(["uptime", "-s"]).decode()
    except: pass

    # Get internal drive space
    free_space = helpers.remaining_space("/")
    if free_space != None:
        internal_drive_space = round(free_space, 3)

    # Get camera drive space
    if config.load() != False:
        if (config.camera_logging == True and
            os.path.isdir(config.camera_directory) and
            os.path.ismount(config.camera_directory)):

            free_space = helpers.remaining_space(config.camera_directory)
            if free_space != None:
                camera_drive_space = round(free_space, 3)

    print(str(startup_time) + str(internal_drive_space) + "\n"
        + str(camera_drive_space))

def operation_shutdown():
    second = datetime.utcnow().second

    while second < 35 or second > 55:
        time.sleep(0.8)
        second = datetime.utcnow().second

    os.system("halt")

def operation_restart():
    second = datetime.utcnow().second

    while second < 35 or second > 55:
        time.sleep(0.8)
        second = datetime.utcnow().second

    os.system("reboot")