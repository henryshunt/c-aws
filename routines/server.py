import os
import subprocess

import routines.config as config
import routines.helpers as helpers

def get_static_info():
    """ Outputs system startup time, and internal and camera drive remaining
        space values
    """
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
        internal_drive_space = round(free_space, 2)

    # Get camera drive space
    if (config.load() == True and config.camera_directory != None and
        os.path.isdir(config.camera_directory) and os.path.ismount(
        config.camera_directory)):

        free_space = helpers.remaining_space(config.camera_directory)
        if free_space != None:
            camera_drive_space = round(free_space, 2)

    # New line needed as startup_time already ends with one
    print(str(startup_time) + str(internal_drive_space) + "\n"
        + str(camera_drive_space))