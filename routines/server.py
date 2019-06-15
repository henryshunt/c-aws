import os
from datetime import datetime
import time
import subprocess

import routines.config as config
import routines.helpers as helpers

def get_startup_time():
    try:
        return subprocess.check_output(["uptime", "-s"])
    except: return "NULL"

def get_internal_drive_space():
    space = helpers.remaining_space("/")
    return "NULL" if space == None else round(space, 3)

def get_camera_drive_space():
    if config.load() == False: return "NULL"

    if (config.camera_logging == True and
        os.path.exists(config.camera_directory) and
        os.path.ismount(config.camera_directory)):

        space = helpers.remaining_space(config.camera_directory)
        return "NULL" if space == None else round(space, 3)
    else: return "NULL"

def do_shutdown():
    second = datetime.utcnow().second

    while second < 35 or second > 55:
        time.sleep(0.8)
        second = datetime.utcnow().second

    os.system("sudo halt")

def do_restart():
    second = datetime.utcnow().second

    while second < 35 or second > 55:
        time.sleep(0.8)
        second = datetime.utcnow().second

    os.system("sudo reboot")