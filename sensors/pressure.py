import statistics

from sensors.logtype import LogType
import sensors.bme280

class Pressure():
    def __init__(self):
        self.__error = False
        self.__log_type = None
        self.__store = None
        self.__shift = None
        self.__bridge = None

    def setup(self, log_type):
        self.__log_type = log_type
        
        try:
            self.__bridge = bme280.BME280(p_mode = bme280.BME280_OSAMPLE_8)
        except: self.__error = True

    def get_error(self):
        return self.__error

    def sample(self):
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
        self.__error = False

        if self.__log_type == LogType.VALUE:
            self.__shift = self.__store

        elif self.__log_type == LogType.ARRAY:
            self.__shift = self.__store[:]

    def __read_value(self):
        try:
            # Temperature must be read first or pressure will not return
            discard_temperature = StaP_sensor.read_temperature()
            return self.__bridge.read_pressure() / 100
        except: raise Exception("Error while reading sensor value")