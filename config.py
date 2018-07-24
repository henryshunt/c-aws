import os
from configparser import ConfigParser

import pytz

class ConfigData():
    def __init__(self):
        self.data_directory = None
        self.database_path = None
        self.camera_drive = None
        self.envReports_logging = None
        self.camera_logging = None
        self.dayStats_generation = None
        self.reports_uploading = None
        self.envReports_uploading = None
        self.dayStats_uploading = None
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
            self.envReports_logging = (parser
                .getboolean("ConfigModifiers", "EnvReportsLogging"))
            self.camera_logging = (parser
                .getboolean("ConfigModifiers", "CameraLogging"))
            self.dayStats_generation = (parser
                .getboolean("ConfigModifiers", "DayStatsGeneration"))
            self.reports_uploading = (parser
                .getboolean("ConfigModifiers", "ReportsUploading"))
            self.envReports_uploading = (parser
                .getboolean("ConfigModifiers", "EnvReportsUploading"))
            self.dayStats_uploading = (parser
                .getboolean("ConfigModifiers", "DayStatsUploading"))
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

        if ((self.envReports_logging == False and
            self.envReports_uploading == True) or
            (self.camera_logging == False and
            self.camera_uploading == True) or
            (self.dayStats_generation == False and
            self.dayStats_uploading == True)):
            return False

        if (self.reports_uploading == True or
            self.envReports_uploading == True or
            self.dayStats_uploading == True):
            
            if self.remote_sql_server == None: return False

        if (self.camera_uploading == True):
            if (self.remote_ftp_server == None or
                self.remote_ftp_username == None or
                self.remote_ftp_password == None):
                return False

        return True
