import os
import configparser

class ConfigData():
    database_path = None

    # Loads the config.ini file from the current directory
    def load(self):
        if not os.path.isfile("config.ini"):
            return False

        parser = configparser.ConfigParser()
        config.read("config.ini")

        database_path = config.get("DataStores", "DatabasePath")
        return True
