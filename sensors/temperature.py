import os
import statistics

from sensors.logtype import LogType

class Temperature():
    def __init__(self):
        self.__error = False

        self.__log_type = None
        self.__address = None
        self.__store = None
    
    def setup(self, log_type, address):
        self.__error = False
        self.__log_type = log_type
        self.__address = address
        self.reset_store()
        
        # Check a probe with that address exists
        if not os.path.isdir("/sys/bus/w1/devices/" + address):
            self.__error = True
            return
    
    def get_error(self):
        return self.__error

    def sample(self):
        self.__error = False

        if self.__log_type == LogType.VALUE:
            try:
                self.__store = self.__read_value()
            except: self.__error = True

        elif self.__log_type == LogType.ARRAY:
            try:
                self.__store.append(self.__read_value())
            except: self.__error = True

    def get_stored(self):
        self.__error = False

        if self.__log_type == LogType.VALUE:
            return self.__store

        elif self.__log_type == LogType.ARRAY:
            if len(self.__store) > 0:
                return statistics.mean(self.__store)

    def reset_store(self):
        self.__error = False
        
        if self.__log_type == LogType.VALUE:
            self.__store = None

        elif self.__log_type == LogType.ARRAY:
            self.__store = []

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