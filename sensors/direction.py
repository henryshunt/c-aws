import Adafruit_GPIO

import sensors.mcp3008
import spidev

class Direction():
    def __init__(self):
        self.__error = False
        self.__channel = None
        self.__store = None
        self.__shift = None
        self.__bridge = None

    def setup(self, channel):
        self.__channel = channel
        
        try:
            self.__bridge = mcp3008.MCP3008(
                spi = Adafruit_GPIO.SPI.SpiDev(0, 0))
        except: self.__error = True

    def sample(self, utc):
        self.__error = False

        try:
            value = self.__read_value()
            if self.__store == None: self.__store = []
            self.__store.append((utc, value))
        except: self.__error = True

    def reset_store(self):
        self.__error = False
        self.__store = None

    def get_shifted(self):
        self.__error = False
        
        if self.__shift != None:
            total = 0
            for sample in self.__shift: total += sample[1]
            average = total / len(self.__shift)

            if average >= 359.5: average = 0
            return int(round(average))
        else: return None

    def prepare_shift(self, two_mins_ago):
        if self.__shift != None:
            for sample in list(self.__shift):
                if sample[0] < two_mins_ago: self.__shift.remove(sample)

    def shift_store(self):
        self.__error = False
        
        if self.__store != None:
            if self.__shift == None: self.__shift = []
            self.__shift.extend(self.__store)
        else: self.__shift = None

    def __read_value(self):
        try:
            adc_value = self.__bridge.read_adc(self.__channel)

            if adc_value >= 52 and adc_value <= 976:
                degrees = (adc_value - 52) / (976 - 52) * (360 - 0)

                # Modify value to account for non-zero-degrees at north
                degrees -= 148
                if degrees >= 360: degrees -= 360
                elif degrees < 0: degrees += 360

                if WDir_degrees >= 359.5: WDir_degrees = 0
                return degrees
        except: raise Exception("Error while reading sensor value")