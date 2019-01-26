import RPi.GPIO as gpio

from sensors.logtype import LogType

class Rainfall():
    def __init__(self):
        self.__error = False

        self.__pin = None
        self.__pause = True
        self.__store = None
        self.__shift = None
    
    def setup(self, pin):
        self.__error = False
        self.__pin = pin
        self.__pause = True

        self.reset_store()
        self.reset_shift()
        
        try:
            gpio.setup(self.__pin, gpio.IN, pull_up_down = gpio.PUD_DOWN)
            gpio.add_event_detect(self.__pin, gpio.FALLING,
                callback = self.__interrupt, bouncetime = 150)
        except: self.__error = True

    def get_error(self):
        return self.__error

    def set_pause(self, pause):
        self.__pause = pause

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

    def __interrupt(self, channel):
        if self.__pause == False:
            self.__store = 1 if self.__store == None else self.__store + 1