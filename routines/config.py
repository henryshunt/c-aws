import os
import json

import pytz


# AWSInfo group
aws_time_zone = None
aws_latitude = None
aws_longitude = None
aws_elevation = None

# DataStores group
data_directory = None
camera_directory = None
main_db_path = None
upload_db_path = None

# DataEndpoints group
remote_sql_server = None
remote_ftp_server = None
remote_ftp_username = None
remote_ftp_password = None

# Operations group
envReport_logging = None
camera_logging = None
dayStat_logging = None
report_uploading = None
envReport_uploading = None
camera_uploading = None
dayStat_uploading = None

# Hardware group
data_led_pin = None
error_led_pin = None
shutdown_pin = None
restart_pin = None

sensors = None


def __validate():
    """ Checks and verifies the loaded configuration values
    """
    global aws_time_zone, aws_latitude, aws_longitude, aws_elevation
    global data_directory, camera_directory, remote_sql_server
    global remote_ftp_server, remote_ftp_username, remote_ftp_password
    global envReport_logging, camera_logging, dayStat_logging, report_uploading
    global envReport_uploading, camera_uploading, dayStat_uploading, AirT, ExpT
    global ExpT_address, RelH, WSpd, WSpd_pin, WDir, WDir_channel, SunD
    global SunD_pin, Rain, Rain_pin, StaP, ST10, ST10_address, ST30
    global ST30_address, ST00, ST00_address

    # AWSInfo group
    if aws_time_zone in pytz.all_timezones:
        aws_time_zone = pytz.timezone(aws_time_zone)
    else: return False

    if aws_latitude < -90 or aws_latitude > 90: return False
    if aws_longitude < -180 or aws_longitude > 180: return False

    # DataStores group
    if camera_logging == True and camera_directory == None: return False

    # Operations group
    if ((envReport_logging == False and envReport_uploading == True) or
        (camera_logging == False and camera_uploading == True) or
        (dayStat_logging == False and dayStat_uploading == True)):
        return False

    if (report_uploading == True or envReport_uploading == True or
        dayStat_uploading == True):
        if remote_sql_server == None: return False

    if camera_uploading == True:
        if (remote_ftp_server == None or remote_ftp_username == None or
            remote_ftp_password == None):
            return False

    # Sensors group        
    if ((ExpT == True and ExpT_address == None) or (ST10 == True and
        ST10_address == None) or (ST30 == True and ST30_address == None) or
        (ST00 == True and ST00_address == None) or (EncT == True and
        EncT_address == None) or (WSpd == True and WSpd_pin == None) or
        (WDir == True and WDir_channel == None) or (SunD == True and
        SunD_pin == None) or (Rain == True and Rain_pin == None)):
        return False

    return True

def load():
    """ Loads data from the config.ini file in the project root directory
    """
    global aws_time_zone, aws_latitude, aws_longitude, aws_elevation
    global data_directory, main_db_path, upload_db_path, camera_directory
    global remote_sql_server, remote_ftp_server, remote_ftp_username
    global remote_ftp_password, envReport_logging, camera_logging
    global dayStat_logging, report_uploading, envReport_uploading
    global camera_uploading, dayStat_uploading, data_led_pin, error_led_pin
    global power_led_pin, shutdown_pin, restart_pin, sensors

    #try:
    with open("/etc/aws.json") as file:
        config = json.load(file)

        # aws_time_zone = __load_value("AWSInfo", "TimeZone", __DataType.STRING, False)
        # aws_latitude = __load_value("AWSInfo", "Latitude", __DataType.FLOAT, False)
        # aws_longitude = __load_value("AWSInfo", "Longitude", __DataType.FLOAT, False)
        # aws_elevation = __load_value("AWSInfo", "Elevation", __DataType.INTEGER, False)

        data_directory = "/var/c-aws"
        main_db_path = os.path.join(data_directory, "data.sq3")
        upload_db_path = os.path.join(data_directory, "upload.sq3")
        # camera_directory = __load_value("DataStores", "CameraDirectory", __DataType.STRING, True)

        # DataEndpoints group
        # remote_sql_server = __load_value(
        #     "DataEndpoints", "RemoteSQLServer", __DataType.STRING, True)
        # remote_ftp_server = __load_value(
        #     "DataEndpoints", "RemoteFTPServer", __DataType.STRING, True)
        # remote_ftp_username = __load_value(
        #     "DataEndpoints", "RemoteFTPUsername", __DataType.STRING, True)
        # remote_ftp_password = __load_value(
        #     "DataEndpoints", "RemoteFTPPassword", __DataType.STRING, True)

        # Operations group
        # envReport_logging = __load_value(
        #     "Operations", "EnvReportLogging", __DataType.BOOLEAN, False)
        # camera_logging = __load_value(
        #     "Operations", "CameraLogging", __DataType.BOOLEAN, False)
        # dayStat_logging = __load_value(
        #     "Operations", "DayStatLogging", __DataType.BOOLEAN, False)
        # report_uploading = __load_value(
        #     "Operations", "ReportUploading", __DataType.BOOLEAN, False)
        # envReport_uploading = __load_value(
        #     "Operations", "EnvReportUploading", __DataType.BOOLEAN, False)
        # camera_uploading = __load_value(
        #     "Operations", "CameraUploading", __DataType.BOOLEAN, False)
        # dayStat_uploading = __load_value(
        #     "Operations", "DayStatUploading", __DataType.BOOLEAN, False)

        
        data_led_pin = config["data_led_pin"]
        error_led_pin = config["error_led_pin"]
        # shutdown_pin = config["shutdown_pin"]
        # restart_pin = config["restart_pin"]

        sensors = config["sensors"]
    #except: return False

    #return False if __validate() == False else True
    return True