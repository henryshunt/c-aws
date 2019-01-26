import RPi.GPIO as gpio

from sensors.logtype import LogType

class Sunshine():
    def __init__(self):
        self.__error = False

        self.__pin = None
        self.__store = None
        self.__shift = None
    
    def setup(self, pin):
        self.__error = False
        self.__pin = pin

        self.reset_store()
        self.reset_shift()
        
        try:
            gpio.setup(25, gpio.IN, pull_up_down = gpio.PUD_DOWN)
        except: self.__error = True

    def get_error(self):
        return self.__error

    def sample(self):
        self.__error = False

        try:
            if self.__store == None:
                self.__store = self.__read_value()
            else: self.__store += self.__read_value()
        except: self.__error = True

    def get_stored(self):
        self.__error = False
        return self.__store

    def reset_store(self):
        self.__error = False
        self.__store = None

    def get_shifted(self):
        self.__error = False
        return self.__shift

    def reset_shift(self):
        self.__error = False
        self.__shift = None

    def shift_store(self):
        self.__error = False
        self.__shift = self.__store

    def __read_value(self):
        try:
            return 1 if gpio.input(self.__pin) == True else 0
        except: raise Exception("Error while reading sensor value")