import os
import configparser

class ConfigData():
    
    def __init__(self):
        """ Initialises instance variables for each config.ini parameter
        """
        self.database_path = None
        self.camera_drive = None
        self.backup_drive = None
        self.camera_logging = None

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
            self.camera_logging = (parser
                .getboolean("ModeSwitches", "CameraLogging"))
        except: return None

        return True
