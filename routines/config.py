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
log_AirT = None
AirT_address = None
log_ExpT = None
ExpT_address = None
log_RelH = None
log_DewP = None
log_WSpd = None
log_WDir = None
log_WGst = None
log_SunD = None
log_Rain = None
log_StaP = None
log_MSLP = None
log_ST10 = None
ST10_address = None
log_ST30 = None
ST30_address = None
log_ST00 = None
ST00_address = None
log_EncT = None
EncT_address = None
log_CPUT = None

def __validate():
    """ Checks the specified values and that interacting options are set
        correctly
    """
    global aws_location, aws_time_zone, data_directory, aws_latitude
    global aws_longitude, database_path, camera_drive_label, camera_drive
    global camera_logging, envReport_logging, envReport_uploading
    global camera_uploading, dayStat_generation, dayStat_uploading
    global report_uploading, remote_sql_server, remote_ftp_server
    global remote_ftp_username, remote_ftp_password, log_AirT, AirT_address
    global log_ExpT, ExpT_address, log_ST10, ST10_address, log_ST30
    global ST30_address, log_ST00, ST00_address, log_EncT, EncT_address

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
    if ((log_AirT == True and AirT_address == None) or (log_ExpT == True and
        ExpT_address == None) or (log_ST10 == True and ST10_address == None) or
        (log_ST30 == True and ST30_address == None) or (log_ST00 == True and
        ST00_address == None) or (log_EncT == True and EncT_address == None)):
        return False

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
    global local_server, log_AirT, AirT_address, log_ExpT, ExpT_address
    global log_RelH, log_DewP, log_WSpd, log_WDir, log_WGst, log_SunD, log_Rain
    global log_StaP, log_MSLP, log_ST10, ST10_address, log_ST30, ST30_address
    global log_ST00, ST00_address, log_EncT, EncT_address, log_CPUT

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
        log_AirT = (__load_value("Sensors", "LogAirT", __DataType.BOOLEAN))
        AirT_address = (
            __load_value("Sensors", "AirTAddress", __DataType.STRING))
        log_ExpT = (__load_value("Sensors", "LogExpT", __DataType.BOOLEAN))
        ExpT_address = (
            __load_value("Sensors", "EncTAddress", __DataType.STRING))
        log_RelH = (__load_value("Sensors", "LogRelH", __DataType.BOOLEAN))
        log_DewP = (__load_value("Sensors", "LogDewP", __DataType.BOOLEAN))
        log_WSpd = (__load_value("Sensors", "LogWSpd", __DataType.BOOLEAN))
        log_WDir = (__load_value("Sensors", "LogWDir", __DataType.BOOLEAN))
        log_WGst = (__load_value("Sensors", "LogWGst", __DataType.BOOLEAN))
        log_SunD = (__load_value("Sensors", "LogSunD", __DataType.BOOLEAN))
        log_Rain = (__load_value("Sensors", "LogRain", __DataType.BOOLEAN))
        log_StaP = (__load_value("Sensors", "LogStaP", __DataType.BOOLEAN))
        log_MSLP = (__load_value("Sensors", "LogMSLP", __DataType.BOOLEAN))
        log_ST10 = (__load_value("Sensors", "LogST10", __DataType.BOOLEAN))
        ST10_address = (
            __load_value("Sensors", "ST10Address", __DataType.STRING))
        log_ST30 = (__load_value("Sensors", "LogST30", __DataType.BOOLEAN))
        ST30_address = (
            __load_value("Sensors", "ST30Address", __DataType.STRING))
        log_ST00 = (__load_value("Sensors", "LogST00", __DataType.BOOLEAN))
        ST00_address = (
            __load_value("Sensors", "ST00Address", __DataType.STRING))
        log_EncT = (__load_value("Sensors", "LogEncT", __DataType.BOOLEAN))
        EncT_address = (
            __load_value("Sensors", "EncTAddress", __DataType.STRING))
        log_CPUT = (__load_value("Sensors", "LogCPUT", __DataType.BOOLEAN))
    except: return False

    return False if __validate() == False else True

class __DataType(Enum):
    BOOLEAN = 1
    FLOAT = 2
    STRING = 3