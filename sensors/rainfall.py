import RPi.GPIO as gpio

class Rainfall():
    def __init__(self):
        self.__error = False
        self.__pin = None
        self.__pause = True
        self.__store = 0
        self.__shift = 0
    
    def setup(self, pin):
        self.__pin = pin
        
        try:
            gpio.setup(pin, gpio.IN, pull_up_down = gpio.PUD_DOWN)
            gpio.add_event_detect(pin, gpio.FALLING,
                callback = self.__interrupt, bouncetime = 150)
        except: self.__error = True

    def get_error(self):
        return self.__error

    def set_pause(self, pause):
        self.__pause = pause

    def get_stored(self):
        self.__error = False
        return self.__store * 0.254

    def reset_store(self):
        self.__error = False
        self.__store = 0

    def get_shifted(self):
        self.__error = False
        return self.__shift * 0.254

    def reset_shift(self):
        self.__error = False
        self.__shift = 0

    def shift_store(self):
        self.__error = False
        self.__shift = self.__store

    def __interrupt(self, channel):
        if self.__pause == False: self.__store += 1