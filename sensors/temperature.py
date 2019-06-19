import os
import statistics

from sensors.logtype import LogType

class Temperature():
    def __init__(self):
        self.__error = False
        self.__log_type = None
        self.__address = None
        self.__store = None
        self.__shift = None
    
    def setup(self, log_type, address):
        self.__log_type = log_type
        self.__address = address
        
        # Check a probe with that address exists
        if not os.path.isdir("/sys/bus/w1/devices/" + address):
            self.__error = True
    
    def get_error(self):
        return self.__error

    def sample(self):
        """ Samples the temperature sensor and stores the value in the store
        """
        self.__error = False

        try:
            value = self.__read_value()

            if self.__log_type == LogType.VALUE:
                self.__store = value

            elif self.__log_type == LogType.ARRAY:
                if self.__store == None: self.__store = []
                self.__store.append(value)
        except: self.__error = True

    def get_stored(self):
        """ Returns the value stored in the store
        """
        self.__error = False

        if self.__log_type == LogType.VALUE:
            return self.__store

        elif self.__log_type == LogType.ARRAY:
            if self.__store != None:
                return statistics.mean(self.__store)
            else: return None

    def reset_store(self):
        self.__error = False
        self.__store = None

    def get_shifted(self):
        """ Returns the value stored in the shifted store
        """
        self.__error = False

        if self.__log_type == LogType.VALUE:
            return self.__shift

        elif self.__log_type == LogType.ARRAY:
            if self.__shift != None:
                return statistics.mean(self.__shift)
            else: return None

    def reset_shift(self):
        self.__error = False
        self.__shift = None

    def shift_store(self):
        """ Shifts the value of the store over to the shift store
        """
        self.__error = False

        if self.__store != None:
            if self.__log_type == LogType.VALUE:
                self.__shift = self.__store

            elif self.__log_type == LogType.ARRAY:
                self.__shift = self.__store[:]
        else: self.__shift = None

    def __read_value(self):
        try:
            # Read the probe and convert its value to a degC float
            with open("/sys/bus/w1/devices/" + self.__address + "/w1_slave", "r"
                    ) as probe:
                data = probe.readlines()
                temp = int(data[1][data[1].find("t=") + 2:]) / 1000

                # Check for error values
                if temp == -127 or temp == 85:
                    raise Exception("Error while reading sensor value")

                return temp
        except: raise Exception("Error while reading sensor value")