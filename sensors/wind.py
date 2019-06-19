from datetime import datetime, timedelta
import statistics

import RPi.GPIO as gpio

class Wind():
    def __init__(self):
        self.__error = False
        self.__pin = None
        self.__pause = True
        self.__store = []
        self.__shift = []

    def setup(self, pin):
        self.__pin = pin
        
        try:
            gpio.setup(pin, gpio.IN, pull_up_down = gpio.PUD_DOWN)
            gpio.add_event_detect(pin, gpio.FALLING,
                callback = self.__interrupt, bouncetime = 1)
        except: self.__error = True

    def get_error(self):
        return self.__error

    def set_pause(self, pause):
        self.__pause = pause

    def reset_store(self):
        self.__error = False
        self.__store = []

    def get_shifted(self, mins_ago, get_gust):
        self.__error = False
        if len(self.__shift) == 0: return 0

        # Return wind speed
        if get_gust == False:
            values = []

            # Iterate over data in three second samples
            for second in range(0, 118, 3):
                start = mins_ago + timedelta(seconds = second)
                end = start + timedelta(seconds = 3)
                ticks_in_sample = 0

                # Calculate three second average wind speed
                for tick in self.__shift:
                    if tick >= start and tick < end: ticks_in_sample += 1

                values.append((ticks_in_sample * 2.5) / 3)
            return statistics.mean(values)

        # Return wind gust
        else:
            value = 0

            # Iterate over each second in three second samples
            for second in range(0, 598):
                start = mins_ago + timedelta(seconds = second)
                end = start + timedelta(seconds = 3)
                ticks_in_sample = 0

                # Calculate 3 second average wind speed, check if highest
                for tick in self.__shift:
                    if tick >= start and tick < end: ticks_in_sample += 1

                sample = (ticks_in_sample * 2.5) / 3
                if sample > value: value = sample
            return value

    def prepare_shift(self, ten_mins_ago):
        """ Prepares the logged data by removing old samples
        """
        if self.__shift != None:
            for tick in list(self.__shift):
                if tick < ten_mins_ago: self.__shift.remove(tick)

    def shift_store(self):
        self.__error = False
        self.__shift.extend(self.__store)

    def __interrupt(self, channel):
        if self.__pause == False:
            self.__store.append(datetime.utcnow())