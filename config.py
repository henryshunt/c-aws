import os
import configparser

class ConfigData():
    
    def __init__(self):
        """ Initialises instance variables for each config.ini parameter
        """
        self.database_path = None
        self.camera_drive = None
        self.backup_drive = None
        self.graph_directory = None

        self.environment_logging = None
        self.camera_logging = None
        self.statistic_generation = None
        self.day_graph_generation = None
        self.month_graph_generation = None
        self.year_graph_generation = None
        self.report_uploading = None
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

            self.database_path = parser.get("DataStores", "DatabasePath")
            self.camera_drive = parser.get("DataStores", "CameraDrive")
            self.backup_drive = parser.get("DataStores", "BackupDrive")
            self.graph_directory = parser.get("DataStores", "GraphDirectory")

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

            self.icaws_identifier = parser.get("ICAWSInfo", "ICAWSIdentifier")
            self.icaws_name = parser.get("ICAWSInfo", "ICAWSName")
            self.icaws_location = parser.get("ICAWSInfo", "ICAWSLocation")
            self.icaws_time_zone = parser.get("ICAWSInfo", "ICAWSTimeZone")
            self.icaws_latitude = parser.get("ICAWSInfo", "ICAWSLatitude")
            self.icaws_longitude = parser.get("ICAWSInfo", "ICAWSLongitude")
            self.icaws_elevation = parser.get("ICAWSInfo", "ICAWSElevation")

            self.remote_sql_server = (parser
                .get("DataEndpoints", "RemoteSQLServer"))
            self.remote_ftp_server = (parser
                .get("DataEndpoints", "RemoteFTPServer"))
            self.remote_ftp_username = (parser
                .get("DataEndpoints", "RemoteFTPUsername"))
            self.remote_ftp_password = (parser
                .get("DataEndpoints", "RemoteFTPPassword"))
        except: return None

        return True
