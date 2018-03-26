import os
import configparser

class ConfigData():
    
    def __init__(self):
        """ Initialises instance variables for each config.ini parameter
        """
        self.database_path = None

    def load(self):
        """ Loads the data from the config.ini file in the current directory
        """
        if not os.path.isfile("config.ini"):
            return False

        parser = configparser.ConfigParser()
        parser.read("config.ini")

        self.database_path = parser.get("DataStores", "DatabasePath")
        return True
