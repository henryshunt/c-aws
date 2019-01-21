import os
from configparser import ConfigParser
from enum import Enum

import pytz

class ConfigData():
    def __init__(self):
        self.__parser = ConfigParser()

        self.aws_location = None
        self.aws_time_zone = None
        self.aws_latitude = None
        self.aws_longitude = None
        self.aws_elevation = None

        self.data_directory = None
        self.database_path = None
        self.camera_drive_label = None
        self.camera_drive = None

        self.remote_sql_server = None
        self.remote_ftp_server = None
        self.remote_ftp_username = None
        self.remote_ftp_password = None

        self.envReport_logging = None
        self.camera_logging = None
        self.dayStat_generation = None
        self.report_uploading = None
        self.envReport_uploading = None
        self.dayStat_uploading = None
        self.camera_uploading = None
        self.local_server = None

        self.log_AirT = None
        self.AirT_address = None
        self.log_ExpT = None
        self.ExpT_address = None
        self.log_RelH = None
        self.log_DewP = None
        self.log_WSpd = None
        self.log_WDir = None
        self.log_WGst = None
        self.log_SunD = None
        self.log_Rain = None
        self.log_StaP = None
        self.log_MSLP = None
        self.log_ST10 = None
        self.ST10_address = None
        self.log_ST30 = None
        self.ST30_address = None
        self.log_ST00 = None
        self.ST00_address = None
        self.log_EncT = None
        self.EncT_address = None
        self.log_CPUT = None

    def load(self):
        """ Loads data from the config.ini file in the current directory
        """

        try:
            self.__parser.read("config.ini")

            # Load AWSInfo group values
            self.aws_location = (
                self.load_value("AWSInfo", "Location", DataType.STRING))
            self.aws_time_zone = (
                self.load_value("AWSInfo", "TimeZone", DataType.STRING))
            self.aws_latitude = (
                self.load_value("AWSInfo", "Latitude", DataType.FLOAT))
            self.aws_longitude = (
                self.load_value("AWSInfo", "Longitude", DataType.FLOAT))
            self.aws_elevation = (
                self.load_value("AWSInfo", "Elevation", DataType.FLOAT))

            # Load DataStores group values
            self.data_directory = self.load_value(
                "DataStores", "DataDirectory", DataType.STRING)
            self.camera_drive_label = self.load_value(
                "DataStores", "CameraDrive", DataType.STRING)

            # Load DataEndpoints group values
            self.remote_sql_server = self.load_value(
                "DataEndpoints", "RemoteSQLServer", DataType.STRING)
            self.remote_ftp_server = self.load_value(
                "DataEndpoints", "RemoteFTPServer", DataType.STRING)
            self.remote_ftp_username = self.load_value(
                "DataEndpoints", "RemoteFTPUsername", DataType.STRING)
            self.remote_ftp_password = self.load_value(
                "DataEndpoints", "RemoteFTPPassword", DataType.STRING)

            # Load Operations group values
            self.envReport_logging = self.load_value(
                "Operations", "EnvReportLogging", DataType.BOOLEAN)
            self.camera_logging = self.load_value(
                "Operations", "CameraLogging", DataType.BOOLEAN)
            self.dayStat_generation = self.load_value(
                "Operations", "DayStatGeneration", DataType.BOOLEAN)
            self.report_uploading = self.load_value(
                "Operations", "ReportUploading", DataType.BOOLEAN)
            self.envReport_uploading = self.load_value(
                "Operations", "EnvReportUploading", DataType.BOOLEAN)
            self.dayStat_uploading = self.load_value(
                "Operations", "DayStatUploading", DataType.BOOLEAN)
            self.camera_uploading = self.load_value(
                "Operations", "CameraUploading", DataType.BOOLEAN)
            self.local_server = self.load_value(
                "Operations", "LocalServer", DataType.BOOLEAN)

            # Load Sensors group values
            self.log_AirT = (
                self.load_value("Sensors", "LogAirT", DataType.BOOLEAN))
            self.AirT_address = (
                self.load_value("Sensors", "AirTAddress", DataType.STRING))
            self.log_ExpT = (
                self.load_value("Sensors", "LogExpT", DataType.BOOLEAN))
            self.ExpT_address = (
                self.load_value("Sensors", "EncTAddress", DataType.STRING))
            self.log_RelH = (
                self.load_value("Sensors", "LogRelH", DataType.BOOLEAN))
            self.log_DewP = (
                self.load_value("Sensors", "LogDewP", DataType.BOOLEAN))
            self.log_WSpd = (
                self.load_value("Sensors", "LogWSpd", DataType.BOOLEAN))
            self.log_WDir = (
                self.load_value("Sensors", "LogWDir", DataType.BOOLEAN))
            self.log_WGst = (
                self.load_value("Sensors", "LogWGst", DataType.BOOLEAN))
            self.log_SunD = (
                self.load_value("Sensors", "LogSunD", DataType.BOOLEAN))
            self.log_Rain = (
                self.load_value("Sensors", "LogRain", DataType.BOOLEAN))
            self.log_StaP = (
                self.load_value("Sensors", "LogStaP", DataType.BOOLEAN))
            self.log_MSLP = (
                self.load_value("Sensors", "LogMSLP", DataType.BOOLEAN))
            self.log_ST10 = (
                self.load_value("Sensors", "LogST10", DataType.BOOLEAN))
            self.ST10_address = (
                self.load_value("Sensors", "ST10Address", DataType.STRING))
            self.log_ST30 = (
                self.load_value("Sensors", "LogST30", DataType.BOOLEAN))
            self.ST30_address = (
                self.load_value("Sensors", "ST30Address", DataType.STRING))
            self.log_ST00 = (
                self.load_value("Sensors", "LogST00", DataType.BOOLEAN))
            self.ST00_address = (
                self.load_value("Sensors", "ST00Address", DataType.STRING))
            self.log_EncT = (
                self.load_value("Sensors", "LogEncT", DataType.BOOLEAN))
            self.EncT_address = (
                self.load_value("Sensors", "EncTAddress", DataType.STRING))
            self.log_CPUT = (
                self.load_value("Sensors", "LogCPUT", DataType.BOOLEAN))
        except: return False

        return False if self.__validate() == False else True

    def load_value(self, group, key, data_type):
        """ Returns the value of the specified key, in the specified type
        """
        if data_type == DataType.BOOLEAN:
            return self.__parser.getboolean(group, key)
        elif data_type == DataType.FLOAT:
            return self.__parser.getfloat(group, key)

        elif data_type == DataType.STRING:
            value = self.__parser.get(group, key)
            return None if value == "" else value

    def __validate(self):
        """ Checks the specified values and that interacting options are set
            correctly
        """

        # AWSInfo group
        if (self.aws_location == None or self.aws_time_zone == None
            or self.data_directory == None):
            return False

        if self.aws_time_zone in pytz.all_timezones:
            self.aws_time_zone = pytz.timezone(self.aws_time_zone)

        if self.aws_latitude < -90 or self.aws_latitude > 90: return False
        if self.aws_location < -180 or self.aws_latitude > 180: return False

        # DataStores group
        self.database_path = os.path.join(self.data_directory, "records.sq3")
        if self.camera_drive_label != None:
            self.camera_drive = "/mnt/" + self.camera_drive_label

        else:
            if self.camera_logging == True: return False

        # Operations group
        if ((self.envReport_logging == False and
            self.envReport_uploading == True) or
            (self.camera_logging == False and
            self.camera_uploading == True) or
            (self.dayStat_generation == False and
            self.dayStat_uploading == True)):
            return False

        if (self.report_uploading == True or
            self.envReport_uploading == True or
            self.dayStat_uploading == True):
            
            if self.remote_sql_server == None: return False

        if (self.camera_uploading == True):
            if (self.remote_ftp_server == None or
                self.remote_ftp_username == None or
                self.remote_ftp_password == None):
                return False

        # Sensors group
        if ((self.log_AirT == True and self.AirT_address == None) or
            (self.log_ExpT == True and self.ExpT_address == None) or
            (self.log_ST10 == True and self.ST10_address == None) or
            (self.log_ST30 == True and self.ST30_address == None) or
            (self.log_ST00 == True and self.ST00_address == None) or
            (self.log_EncT == True and self.EncT_address == None)):
            return False

        return True

class DataType(Enum):
    BOOLEAN = 1
    FLOAT = 2
    STRING = 3
