import os
from configparser import ConfigParser

import pytz

class ConfigData():
    def __init__(self):
        self.data_directory = None
        self.database_path = None
        self.camera_drive = None
        self.envReport_logging = None
        self.camera_logging = None
        self.dayStat_generation = None
        self.report_uploading = None
        self.envReport_uploading = None
        self.dayStat_uploading = None
        self.camera_uploading = None
        self.local_network_server = None
        self.aws_location = None
        self.aws_time_zone = None
        self.aws_elevation = None
        self.aws_latitude = None
        self.aws_longitude = None
        self.remote_sql_server = None
        self.remote_ftp_server = None
        self.remote_ftp_username = None
        self.remote_ftp_password = None

    def load(self):
        """ Loads data from the config.ini file in the current directory
        """
        if not os.path.isfile("config.ini"): return False

        try:
            parser = ConfigParser(); parser.read("config.ini")

            # Check required configuration options
            self.data_directory = parser.get("DataStores", "DataDirectory")
            if self.data_directory == "": return False
            self.aws_location = parser.get("AWSInfo", "Location")
            if self.aws_location == "": return False

            self.aws_time_zone = parser.get("AWSInfo", "TimeZone")
            if not self.aws_time_zone in pytz.all_timezones: return False
            self.aws_time_zone = pytz.timezone(self.aws_time_zone)

            self.aws_elevation = parser.getfloat("AWSInfo", "Elevation")
            self.aws_latitude = parser.getfloat("AWSInfo", "Latitude")
            self.aws_longitude = parser.getfloat("AWSInfo", "Longitude")

            # Derive directories and file paths
            self.database_path = os.path.join(self.data_directory,
                "records.sq3")
            
            # Load non-required configuration options
            self.camera_drive = parser.get("DataStores", "CameraDrive")
            if self.camera_drive == "": self.camera_drive = None

            self.remote_sql_server = (parser.get("DataEndpoints",
                "RemoteSQLServer"))
            if self.remote_sql_server == "": self.remote_sql_server = None
            self.remote_ftp_server = (parser.get("DataEndpoints",
                "RemoteFTPServer"))
            if self.remote_ftp_server == "": self.remote_ftp_server = None
            self.remote_ftp_username = (parser.get("DataEndpoints",
                "RemoteFTPUsername"))
            if self.remote_ftp_username == "": self.remote_ftp_username = None
            self.remote_ftp_password = (parser.get("DataEndpoints",
                "RemoteFTPPassword"))
            if self.remote_ftp_password == "": self.remote_ftp_password = None
            
            # Load boolean configuration modifiers
            self.envReport_logging = (parser
                .getboolean("ConfigModifiers", "EnvReportLogging"))
            self.camera_logging = (parser
                .getboolean("ConfigModifiers", "CameraLogging"))
            self.dayStat_generation = (parser
                .getboolean("ConfigModifiers", "DayStatGeneration"))
            self.report_uploading = (parser
                .getboolean("ConfigModifiers", "ReportUploading"))
            self.envReport_uploading = (parser
                .getboolean("ConfigModifiers", "EnvReportUploading"))
            self.dayStat_uploading = (parser
                .getboolean("ConfigModifiers", "DayStatUploading"))
            self.camera_uploading = (parser
                .getboolean("ConfigModifiers", "CameraUploading"))
            self.local_network_server = (parser
                .getboolean("ConfigModifiers", "LocalNetworkServer"))
        except: return False

        return True

    def validate(self):
        """ Checks if options needed for other options are set correctly
        """
        if (self.camera_logging == True and
            self.camera_drive == None):
            return False

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

        return True
