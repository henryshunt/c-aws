from gpiozero import CPUTemperature

class Processor():
    def __init__(self):
        self.__error = False
        self.__store = None

    def get_error(self):
        return self.__error

    def sample(self):
        try:
            self.__store = self.__read_value()
        except: self.__error = True

    def get_stored(self):
        self.__error = False
        return self.__store

    def __read_value(self):
        try:
            return CPUTemperature().temperature
        except: raise Exception("Error while reading sensor value")