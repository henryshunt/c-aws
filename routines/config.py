import os
from configparser import ConfigParser
from enum import Enum

import pytz

__parser = ConfigParser()

# AWSInfo group
aws_location = None
aws_time_zone = None
aws_latitude = None
aws_longitude = None
aws_elevation = None

# DataStores group
data_directory = None
database_path = None
camera_drive_label = None
camera_drive = None

# DataEndpoints group
remote_sql_server = None
remote_ftp_server = None
remote_ftp_username = None
remote_ftp_password = None

# Operations group
envReport_logging = None
camera_logging = None
dayStat_generation = None
report_uploading = None
envReport_uploading = None
dayStat_uploading = None
camera_uploading = None
local_server = None

# Sensors group
AirT = None
AirT_address = None
ExpT = None
ExpT_address = None
RelH = None
WSpd = None
WDir = None
SunD = None
Rain = None
StaP = None
ST10 = None
ST10_address = None
ST30 = None
ST30_address = None
ST00 = None
ST00_address = None
EncT = None
EncT_address = None

# Derived group
log_DewP = None
log_WGst = None
log_MSLP = None

def __validate():
    """ Checks the specified values and that interacting options are set
        correctly
    """
    global aws_location, aws_time_zone, data_directory, aws_latitude
    global aws_longitude, database_path, camera_drive_label, camera_drive
    global camera_logging, envReport_logging, envReport_uploading
    global camera_uploading, dayStat_generation, dayStat_uploading
    global report_uploading, remote_sql_server, remote_ftp_server
    global remote_ftp_username, remote_ftp_password, AirT, AirT_address
    global ExpT, ExpT_address, ST10, ST10_address, ST30, ST30_address, ST00
    global ST00_address, EncT, EncT_address, log_DewP, RelH, log_WGst, WSpd
    global log_MSLP, StaP

    # AWSInfo group
    if aws_location == None or aws_time_zone == None or data_directory == None:
        return False

    if aws_time_zone in pytz.all_timezones:
        aws_time_zone = pytz.timezone(aws_time_zone)

    if aws_latitude < -90 or aws_latitude > 90: return False
    if aws_longitude < -180 or aws_longitude > 180: return False

    # DataStores group
    database_path = os.path.join(data_directory, "records.sq3")
    if camera_drive_label != None:
        camera_drive = "/mnt/" + camera_drive_label

    else:
        if camera_logging == True: return False

    # Operations group
    if ((envReport_logging == False and envReport_uploading == True) or
        (camera_logging == False and camera_uploading == True) or
        (dayStat_generation == False and dayStat_uploading == True)):
        return False

    if (report_uploading == True or envReport_uploading == True or
        dayStat_uploading == True):
        
        if remote_sql_server == None: return False

    if (camera_uploading == True):
        if (remote_ftp_server == None or remote_ftp_username == None or
            remote_ftp_password == None):
            return False

    # Sensors group
    if ((AirT == True and AirT_address == None) or (ExpT == True and
        ExpT_address == None) or (ST10 == True and ST10_address == None) or
        (ST30 == True and ST30_address == None) or (ST00 == True and
        ST00_address == None) or (EncT == True and EncT_address == None)):
        return False

    # Derived group
    if log_DewP == True and (AirT == False or RelH == False): return False
    if log_WGst == True and WSpd == False: return False
    if log_MSLP == True and (StaP == False or AirT == False or
        log_DewP == False): return False

    return True

def __load_value(group, key, data_type):
    """ Returns the value of the specified key, in the specified type
    """
    global __parser

    if data_type == __DataType.BOOLEAN:
        return __parser.getboolean(group, key)
    elif data_type == __DataType.FLOAT:
        return __parser.getfloat(group, key)

    elif data_type == __DataType.STRING:
        value = __parser.get(group, key)
        return None if value == "" else value

def load():
    """ Loads data from the config.ini file in the current directory
    """
    global __parser, aws_location, aws_time_zone, aws_latitude, aws_longitude
    global aws_elevation, data_directory, database_path, camera_drive_label
    global camera_drive, remote_sql_server, remote_ftp_server
    global remote_ftp_username, remote_ftp_password, envReport_logging
    global camera_logging, dayStat_generation, report_uploading
    global envReport_uploading, dayStat_uploading, camera_uploading
    global local_server, AirT, AirT_address, ExpT, ExpT_address, RelH, WSpd
    global WDir, SunD, Rain, StaP, ST10, ST10_address, ST30, ST30_address, ST00
    global ST00_address, EncT, EncT_address, log_DewP, log_WGst, log_MSLP

    try:
        __parser.read("config.ini")

        # Load AWSInfo group values
        aws_location = __load_value("AWSInfo", "Location", __DataType.STRING)
        aws_time_zone = __load_value("AWSInfo", "TimeZone", __DataType.STRING)
        aws_latitude = __load_value("AWSInfo", "Latitude", __DataType.FLOAT)
        aws_longitude = __load_value("AWSInfo", "Longitude", __DataType.FLOAT)
        aws_elevation = __load_value("AWSInfo", "Elevation", __DataType.FLOAT)

        # Load DataStores group values
        data_directory = __load_value(
            "DataStores", "DataDirectory", __DataType.STRING)
        camera_drive_label = __load_value(
            "DataStores", "CameraDrive", __DataType.STRING)

        # Load DataEndpoints group values
        remote_sql_server = __load_value(
            "DataEndpoints", "RemoteSQLServer", __DataType.STRING)
        remote_ftp_server = __load_value(
            "DataEndpoints", "RemoteFTPServer", __DataType.STRING)
        remote_ftp_username = __load_value(
            "DataEndpoints", "RemoteFTPUsername", __DataType.STRING)
        remote_ftp_password = __load_value(
            "DataEndpoints", "RemoteFTPPassword", __DataType.STRING)

        # Load Operations group values
        envReport_logging = __load_value(
            "Operations", "EnvReportLogging", __DataType.BOOLEAN)
        camera_logging = __load_value(
            "Operations", "CameraLogging", __DataType.BOOLEAN)
        dayStat_generation = __load_value(
            "Operations", "DayStatGeneration", __DataType.BOOLEAN)
        report_uploading = __load_value(
            "Operations", "ReportUploading", __DataType.BOOLEAN)
        envReport_uploading = __load_value(
            "Operations", "EnvReportUploading", __DataType.BOOLEAN)
        dayStat_uploading = __load_value(
            "Operations", "DayStatUploading", __DataType.BOOLEAN)
        camera_uploading = __load_value(
            "Operations", "CameraUploading", __DataType.BOOLEAN)
        local_server = __load_value(
            "Operations", "LocalServer", __DataType.BOOLEAN)

        # Load Sensors group values
        AirT = (__load_value("Sensors", "AirT", __DataType.BOOLEAN))
        AirT_address = (
            __load_value("Sensors", "AirTAddress", __DataType.STRING))
        ExpT = (__load_value("Sensors", "ExpT", __DataType.BOOLEAN))
        ExpT_address = (
            __load_value("Sensors", "ExpTAddress", __DataType.STRING))
        RelH = (__load_value("Sensors", "RelH", __DataType.BOOLEAN))
        WSpd = (__load_value("Sensors", "WSpd", __DataType.BOOLEAN))
        WDir = (__load_value("Sensors", "WDir", __DataType.BOOLEAN))
        SunD = (__load_value("Sensors", "SunD", __DataType.BOOLEAN))
        Rain = (__load_value("Sensors", "Rain", __DataType.BOOLEAN))
        StaP = (__load_value("Sensors", "StaP", __DataType.BOOLEAN))
        ST10 = (__load_value("Sensors", "ST10", __DataType.BOOLEAN))
        ST10_address = (
            __load_value("Sensors", "ST10Address", __DataType.STRING))
        ST30 = (__load_value("Sensors", "ST30", __DataType.BOOLEAN))
        ST30_address = (
            __load_value("Sensors", "ST30Address", __DataType.STRING))
        ST00 = (__load_value("Sensors", "ST00", __DataType.BOOLEAN))
        ST00_address = (
            __load_value("Sensors", "ST00Address", __DataType.STRING))
        EncT = (__load_value("Sensors", "EncT", __DataType.BOOLEAN))
        EncT_address = (
            __load_value("Sensors", "EncTAddress", __DataType.STRING))

        # Load Derived group values
        log_DewP = (__load_value("Derived", "LogDewP", __DataType.BOOLEAN))
        log_WGst = (__load_value("Derived", "LogWGst", __DataType.BOOLEAN))
        log_MSLP = (__load_value("Derived", "LogMSLP", __DataType.BOOLEAN))
    except: return False

    return False if __validate() == False else True

class __DataType(Enum):
    BOOLEAN = 1
    FLOAT = 2
    STRING = 3