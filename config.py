import os
from configparser import ConfigParser
import pytz

class ConfigData():
    
    def __init__(self):
        """ Initialises instance variables for each config.ini parameter
        """
        self.data_directory = None
        self.database_path = None
        self.graph_directory = None
        self.integrity_path = None
        self.camera_drive = None
        self.backup_drive = None
        self.environment_logging = None
        self.camera_logging = None
        self.statistic_generation = None
        self.day_graph_generation = None
        self.month_graph_generation = None
        self.year_graph_generation = None
        self.report_uploading = None
        self.environment_uploading = None
        self.statistic_uploading = None
        self.camera_uploading = None
        self.day_graph_uploading = None
        self.month_graph_uploading = None
        self.year_graph_uploading = None
        self.integrity_checks = None
        self.local_network_server = None
        self.backups = None
        self.icaws_identifier = None
        self.icaws_name = None
        self.icaws_location = None
        self.icaws_time_zone = None
        self.icaws_latitude = None
        self.icaws_longitude = None
        self.icaws_elevation = None
        self.remote_sql_server = None
        self.remote_ftp_server = None
        self.remote_ftp_username = None
        self.remote_ftp_password = None

    def load(self):
        """ Loads the data from the config.ini file in the current directory
        """
        if not os.path.isfile("config.ini"): return False

        try:
            parser = ConfigParser(); parser.read("config.ini")

            # Check required configuration options
            self.data_directory = parser.get("DataStores", "DataDirectory")
            if self.data_directory == "": return False
            self.icaws_name = parser.get("ICAWSInfo", "ICAWSName")
            if self.icaws_name == "": return False
            self.icaws_location = parser.get("ICAWSInfo", "ICAWSLocation")
            if self.icaws_location == "": return False
            self.icaws_time_zone = parser.get("ICAWSInfo", "ICAWSTimeZone")
            if not self.icaws_time_zone in pytz.all_timezones: return False
            self.icaws_latitude = parser.getfloat("ICAWSInfo", "ICAWSLatitude")
            self.icaws_longitude = (parser
                .getfloat("ICAWSInfo", "ICAWSLongitude"))
            self.icaws_elevation = (parser
                .getfloat("ICAWSInfo", "ICAWSElevation"))

            # Derive directories and file paths
            self.database_path = os.path.join(
                self.data_directory, "records.sq3")
            self.graph_directory = os.path.join(self.data_directory, "graphs")
            self.integrity_path = os.path.join(
                self.data_directory, "integrity.xml")
            
            # Load non-required configuration options
            self.camera_drive = parser.get("DataStores", "CameraDrive")
            if self.camera_drive == "": self.camera_drive = None
            self.backup_drive = parser.get("DataStores", "BackupDrive")
            if self.backup_drive == "": self.backup_drive = None
            
            # Load boolean configuration modifiers
            self.environment_logging = (parser
                .getboolean("ConfigModifiers", "EnvironmentLogging"))
            self.camera_logging = (parser
                .getboolean("ConfigModifiers", "CameraLogging"))
            self.statistic_generation = (parser
                .getboolean("ConfigModifiers", "StatisticGeneration"))
            self.day_graph_generation = (parser
                .getboolean("ConfigModifiers", "DayGraphGeneration"))
            self.month_graph_generation = (parser
                .getboolean("ConfigModifiers", "MonthGraphGeneration"))
            self.year_graph_generation = (parser
                .getboolean("ConfigModifiers", "YearGraphGeneration"))
            self.report_uploading = (parser
                .getboolean("ConfigModifiers", "ReportUploading"))
            self.environment_uploading = (parser
                .getboolean("ConfigModifiers", "EnvironmentUploading"))
            self.statistic_uploading = (parser
                .getboolean("ConfigModifiers", "StatisticUploading"))
            self.camera_uploading = (parser
                .getboolean("ConfigModifiers", "CameraUploading"))
            self.day_graph_uploading = (parser
                .getboolean("ConfigModifiers", "DayGraphUploading"))
            self.month_graph_uploading = (parser
                .getboolean("ConfigModifiers", "MonthGraphUploading"))
            self.year_graph_uploading = (parser
                .getboolean("ConfigModifiers", "YearGraphUploading"))
            self.integrity_checks = (parser
                .getboolean("ConfigModifiers", "IntegrityChecks"))
            self.local_network_server = (parser
                .getboolean("ConfigModifiers", "LocalNetworkServer"))
            self.backups = parser.getboolean("ConfigModifiers", "Backups")
            
            # Load non-required configuration options
            self.remote_sql_server = (parser
                .get("DataEndpoints", "RemoteSQLServer"))
            if self.remote_sql_server == "": self.remote_sql_server = None
            
            self.remote_ftp_server = (parser
                .get("DataEndpoints", "RemoteFTPServer"))
            if self.remote_ftp_server == "": self.remote_ftp_server = None

            self.remote_ftp_username = (parser
                .get("DataEndpoints", "RemoteFTPUsername"))
            if self.remote_ftp_username == "": self.remote_ftp_username = None

            self.remote_ftp_password = (parser
                .get("DataEndpoints", "RemoteFTPPassword"))
            if self.remote_ftp_password == "": self.remote_ftp_password = None
        except: return False
        return True

    def validate(self):
        if (self.camera_logging == True and
            self.camera_drive == None):
            return False

        if (self.backups == True and
            self.backup_drive == None):
            return False

        if (self.statistic_generation == False and
            (self.month_graph_generation == True or
             self.year_graph_generation == True)):
             return False

        if ((self.environment_logging == False and
            self.environment_uploading == True) or
            (self.camera_logging == False and
            self.camera_uploading == True) or
            (self.statistic_generation == False and
            self.statistic_uploading == True) or
            (self.day_graph_generation == False and
            self.day_graph_uploading == True) or
            (self.month_graph_generation == False and
            self.month_graph_uploading == True) or
            (self.year_graph_generation == False and
            self.year_graph_uploading == True)):
            return False

        if (self.report_uploading == True or
            self.environment_uploading == True or
            self.statistic_uploading == True):

            if self.remote_sql_server == None: return False

        if (self.camera_uploading == True or
            self.day_graph_uploading == True or
            self.month_graph_uploading == True or
            self.year_graph_uploading == True):

            if (self.remote_ftp_server == None or
                self.remote_ftp_username == None or
                self.remote_ftp_password == None):
                return False

        return True
