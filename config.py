import os
import configparser

class ConfigData():
    
    def __init__(self):
        self.database_path = None

    # Loads the config.ini file from the current directory
    def load(self):
        if not os.path.isfile("config.ini"):
            return False

        parser = configparser.ConfigParser()
        parser.read("config.ini")

        self.database_path = parser.get("DataStores", "DatabasePath")
        return True
