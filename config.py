import os
import configparser

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
        if not os.path.isfile("config.ini"): return None

        try:
            parser = configparser.ConfigParser()
            parser.read("config.ini")

            self.data_directory = parser.get("DataStores", "DataDirectory")
            
            if self.data_directory == "NULL":
                self.data_directory = None
                self.database_path = None
                self.graph_directory = None
                self.integrity_path = None
            else:
                self.database_path = os.path.join(self.data_directory,
                                                  "records.sq3")
                self.graph_directory = os.path.join(self.data_directory,
                                                    "graphs")
                self.integrity_path = os.path.join(self.data_directory,
                                                   "integrity.xml")
            
            self.camera_drive = parser.get("DataStores", "CameraDrive")
            if self.camera_drive == "NULL": self.camera_drive = None
            
            self.backup_drive = parser.get("DataStores", "BackupDrive")
            if self.backup_drive == "NULL": self.backup_drive = None
            
            self.environment_logging = parser.getboolean("ConfigModifiers",
                                                         "EnvironmentLogging")
            self.camera_logging = parser.getboolean("ConfigModifiers",
                                                    "CameraLogging")
            self.statistic_generation = parser.getboolean("ConfigModifiers",
                                                          "StatisticGeneration")
            self.day_graph_generation = parser.getboolean("ConfigModifiers",
                                                          "DayGraphGeneration")
            self.month_graph_generation = parser.getboolean(
                "ConfigModifiers", "MonthGraphGeneration")
            self.year_graph_generation = parser.getboolean(
                "ConfigModifiers", "YearGraphGeneration")
            self.report_uploading = parser.getboolean("ConfigModifiers",
                                                      "ReportUploading")
            self.environment_uploading = parser.getboolean(
                "ConfigModifiers", "EnvironmentUploading")
            self.statistic_uploading = parser.getboolean("ConfigModifiers",
                                                         "StatisticUploading")
            self.camera_uploading = parser.getboolean("ConfigModifiers",
                                                      "CameraUploading")
            self.day_graph_uploading = parser.getboolean("ConfigModifiers",
                                                         "DayGraphUploading")
            self.month_graph_uploading = parser.getboolean(
                "ConfigModifiers", "MonthGraphUploading")
            self.year_graph_uploading = parser.getboolean("ConfigModifiers",
                                                          "YearGraphUploading")
            self.integrity_checks = parser.getboolean("ConfigModifiers",
                                                      "IntegrityChecks")
            self.local_network_server = parser.getboolean("ConfigModifiers",
                                                          "LocalNetworkServer")
            self.backups = parser.getboolean("ConfigModifiers", "Backups")

            self.icaws_identifier = parser.get("ICAWSInfo", "ICAWSIdentifier")
            if self.icaws_identifier == "NULL": self.icaws_identifier = None
            
            self.icaws_name = parser.get("ICAWSInfo", "ICAWSName")
            if self.icaws_name == "NULL": self.icaws_name = None
            
            self.icaws_location = parser.get("ICAWSInfo", "ICAWSLocation")
            if self.icaws_location == "NULL": self.icaws_location = None
            
            self.icaws_time_zone = parser.get("ICAWSInfo", "ICAWSTimeZone")
            if self.icaws_time_zone == "NULL": self.icaws_time_zone = None
            
            self.icaws_latitude = parser.get("ICAWSInfo", "ICAWSLatitude")
            if self.icaws_latitude == "NULL": self.icaws_latitude = None
            
            self.icaws_longitude = parser.get("ICAWSInfo", "ICAWSLongitude")
            if self.icaws_longitude == "NULL": self.icaws_longitude = None
            
            self.icaws_elevation = parser.get("ICAWSInfo", "ICAWSElevation")
            if self.icaws_elevation == "NULL": self.icaws_elevation = None
            
            self.remote_sql_server = parser.get("DataEndpoints",
                                                "RemoteSQLServer")
            if self.remote_sql_server == "NULL": self.remote_sql_server = None
            
            self.remote_ftp_server = parser.get("DataEndpoints",
                                                "RemoteFTPServer")
            if self.remote_ftp_server == "NULL": self.remote_ftp_server = None

            self.remote_ftp_username = parser.get("DataEndpoints",
                                                  "RemoteFTPUsername")
            if self.remote_ftp_username == "NULL":
                self.remote_ftp_username = None

            self.remote_ftp_password = parser.get("DataEndpoints",
                                                  "RemoteFTPPassword")
            if self.remote_ftp_password == "NULL":
                self.remote_ftp_password = None
        except: return None

        return True
