import os
import subprocess

import routines.config as config
import routines.helpers as helpers

def get_static_info():
    """ Outputs system startup time, and internal and camera drive remaining
        space values
    """
    startup_time = None
    data_drive_space = None
    camera_drive_space = None
    
    # Get system startup time
    try:
        startup_time = (subprocess
            .check_output(["uptime", "-s"]).decode().rstrip())
    except: pass

    # Get data and camera drive space
    if config.load() == True:
        if os.path.isdir(config.data_directory):
            free_space = helpers.remaining_space(config.data_directory)

            if free_space != None:
                data_drive_space = round(free_space, 2)

        if (config.camera_directory != None and os.path.isdir(
            config.camera_directory) and os.path.ismount(
            config.camera_directory)):

            free_space = helpers.remaining_space(config.camera_directory)
            if free_space != None:
                camera_drive_space = round(free_space, 2)

    print(str(helpers.none_to_null(startup_time)) + "\n"
        + str(helpers.none_to_null(data_drive_space)) + "\n"
        + str(helpers.none_to_null(camera_drive_space)))