from enum import Enum

class Sensor():
    def __init__(self):
        self.log_type = None
        self.address = None
        self.primary = None
        self.secondary = None
    
    def setup(self, log_type):
        self.log_type = log_type

    def sample(self):
        """ Samples the sensor and stores the value in the primary data store
        """
        value = self.read_value()

        if self.log_type == LogType.VALUE:
            self.primary = value
        elif self.log_type == LogType.ARRAY:
            if self.primary == None: self.primary = []
            self.primary.append(value)

        
    def get_primary(self):
        """ Returns the value stored in the primary data store
        """        
        if self.log_type == LogType.VALUE:
            return self.primary
        elif self.log_type == LogType.ARRAY:
            return self.array_format(self.primary)

    def reset_primary(self):
        self.primary = None

    def get_secondary(self):
        """ Returns the value stored in the secondary data store
        """
        if self.log_type == LogType.VALUE:
            return self.secondary
        elif self.log_type == LogType.ARRAY:
            return self.array_format(self.secondary)

    def reset_secondary(self):
        self.secondary = None

    def shift(self):
        """ Shifts the primary data store into the secondary data store
        """
        if self.primary != None:
            if self.log_type == LogType.VALUE:
                self.secondary = self.primary

            elif self.log_type == LogType.ARRAY:
                self.secondary = self.primary[:]
        else: self.secondary = None


    def read_value(self):
        """ Reads a value from the sensor
        """
        raise NotImplementedError("Must override read_value")

    def array_format(self, array):
        """ Creates the final value when using LogType.ARRAY
        """
        raise NotImplementedError("Must override array_format")

class LogType(Enum):
    VALUE = 1
    ARRAY = 2