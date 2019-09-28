import os
from configparser import ConfigParser
from enum import Enum

import pytz


__parser = ConfigParser()

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
power_led_pin = None
shutdown_pin = None
restart_pin = None

# Sensors group
AirT = None
ExpT = None
ExpT_address = None
RelH = None
WSpd = None
WSpd_pin = None
WDir = None
WDir_channel = None
WDir_offset = None
SunD = None
SunD_pin = None
Rain = None
Rain_pin = None
StaP = None
ST10 = None
ST10_address = None
ST30 = None
ST30_address = None
ST00 = None
ST00_address = None
EncT = None
EncT_address = None


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
    global ST30_address, ST00, ST00_address, EncT, EncT_address

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

def __load_value(group, key, data_type, none_ok):
    """ Returns the value of the specified key, in the specified type
    """
    global __parser

    value = __parser.get(group, key)
    if value == "" and none_ok == True:
        return None
    elif value == "" and none_ok == False:
        raise Exception("None value cannot be None")

    if data_type == __DataType.STRING:
        return __parser.get(group, key)
    elif data_type == __DataType.BOOLEAN:
        return __parser.getboolean(group, key)
    elif data_type == __DataType.INTEGER:
        return __parser.getint(group, key)
    elif data_type == __DataType.FLOAT:
        return __parser.getfloat(group, key)

def load():
    """ Loads data from the config.ini file in the project root directory
    """
    global __parser, aws_time_zone, aws_latitude, aws_longitude, aws_elevation
    global data_directory, main_db_path, upload_db_path, camera_directory
    global remote_sql_server, remote_ftp_server, remote_ftp_username
    global remote_ftp_password, envReport_logging, camera_logging
    global dayStat_logging, report_uploading, envReport_uploading
    global camera_uploading, dayStat_uploading, data_led_pin, error_led_pin
    global power_led_pin, shutdown_pin, restart_pin, AirT, ExpT, ExpT_address
    global RelH, WSpd, WSpd_pin, WDir, WDir_channel, WDir_offset, SunD, SunD_pin
    global Rain, Rain_pin, StaP, ST10, ST10_address, ST30, ST30_address, ST00
    global ST00_address, EncT, EncT_address

    try:
        __parser.read("config.ini")

        # AWSInfo group
        aws_time_zone = __load_value("AWSInfo", "TimeZone", __DataType.STRING,
            False)
        aws_latitude = __load_value("AWSInfo", "Latitude", __DataType.FLOAT,
            False)
        aws_longitude = __load_value("AWSInfo", "Longitude", __DataType.FLOAT,
            False)
        aws_elevation = __load_value("AWSInfo", "Elevation", __DataType.INTEGER,
            False)

        # DataStores group
        data_directory = __load_value(
            "DataStores", "DataDirectory", __DataType.STRING, False)
        main_db_path = os.path.join(data_directory, "data.sq3")
        upload_db_path = os.path.join(data_directory, "upload.sq3")
        camera_directory = __load_value(
            "DataStores", "CameraDirectory", __DataType.STRING, True)

        # DataEndpoints group
        remote_sql_server = __load_value(
            "DataEndpoints", "RemoteSQLServer", __DataType.STRING, True)
        remote_ftp_server = __load_value(
            "DataEndpoints", "RemoteFTPServer", __DataType.STRING, True)
        remote_ftp_username = __load_value(
            "DataEndpoints", "RemoteFTPUsername", __DataType.STRING, True)
        remote_ftp_password = __load_value(
            "DataEndpoints", "RemoteFTPPassword", __DataType.STRING, True)

        # Operations group
        envReport_logging = __load_value(
            "Operations", "EnvReportLogging", __DataType.BOOLEAN, False)
        camera_logging = __load_value(
            "Operations", "CameraLogging", __DataType.BOOLEAN, False)
        dayStat_logging = __load_value(
            "Operations", "DayStatLogging", __DataType.BOOLEAN, False)
        report_uploading = __load_value(
            "Operations", "ReportUploading", __DataType.BOOLEAN, False)
        envReport_uploading = __load_value(
            "Operations", "EnvReportUploading", __DataType.BOOLEAN, False)
        camera_uploading = __load_value(
            "Operations", "CameraUploading", __DataType.BOOLEAN, False)
        dayStat_uploading = __load_value(
            "Operations", "DayStatUploading", __DataType.BOOLEAN, False)

        # Hardware group
        data_led_pin = __load_value(
            "Hardware", "DataLEDPin", __DataType.INTEGER, True)
        error_led_pin = __load_value(
            "Hardware", "ErrorLEDPin", __DataType.INTEGER, True)
        power_led_pin = __load_value(
            "Hardware", "PowerLEDPin", __DataType.INTEGER, True)
        shutdown_pin = __load_value(
            "Hardware", "ShutdownPin", __DataType.INTEGER, True)
        restart_pin = __load_value(
            "Hardware", "RestartPin", __DataType.INTEGER, True)

        # Sensors group
        AirT = __load_value("Sensors", "AirT", __DataType.BOOLEAN, False)
        ExpT = __load_value("Sensors", "ExpT", __DataType.BOOLEAN, False)
        ExpT_address = (
            __load_value("Sensors", "ExpTAddress", __DataType.STRING, True))
        RelH = __load_value("Sensors", "RelH", __DataType.BOOLEAN, False)
        WSpd = __load_value("Sensors", "WSpd", __DataType.BOOLEAN, False)
        WSpd_pin = __load_value("Sensors", "WSpdPin", __DataType.INTEGER, True)
        WDir = __load_value("Sensors", "WDir", __DataType.BOOLEAN, False)
        WDir_channel = (
            __load_value("Sensors", "WDirChannel", __DataType.INTEGER, True))
        WDir_offset = (
            __load_value("Sensors", "WDirOffset", __DataType.INTEGER, True))
        SunD = __load_value("Sensors", "SunD", __DataType.BOOLEAN, False)
        SunD_pin = __load_value("Sensors", "SunDPin", __DataType.INTEGER, True)
        Rain = __load_value("Sensors", "Rain", __DataType.BOOLEAN, False)
        Rain_pin = __load_value("Sensors", "RainPin", __DataType.INTEGER, True)
        StaP = __load_value("Sensors", "StaP", __DataType.BOOLEAN, False)
        ST10 = __load_value("Sensors", "ST10", __DataType.BOOLEAN, False)
        ST10_address = (
            __load_value("Sensors", "ST10Address", __DataType.STRING, True))
        ST30 = __load_value("Sensors", "ST30", __DataType.BOOLEAN, False)
        ST30_address = (
            __load_value("Sensors", "ST30Address", __DataType.STRING, True))
        ST00 = __load_value("Sensors", "ST00", __DataType.BOOLEAN, False)
        ST00_address = (
            __load_value("Sensors", "ST00Address", __DataType.STRING, True))
        EncT = __load_value("Sensors", "EncT", __DataType.BOOLEAN, False)
        EncT_address = (
            __load_value("Sensors", "EncTAddress", __DataType.STRING, True))
    except: return False

    return False if __validate() == False else True

class __DataType(Enum):
    BOOLEAN = 1
    FLOAT = 2
    STRING = 3
    INTEGER = 4