import statistics

import board
import busio
import adafruit_htu21d

from sensors.sensor import Sensor

class HTU21D(Sensor):

    def setup(self, log_type):
        super().setup(log_type)

        i2c = busio.I2C(board.SCL, board.SDA)
        self.bridge = adafruit_htu21d.HTU21D(i2c)

    def read_value(self):
        return self.bridge.relative_humidity

    def array_format(self, array):
        if array != None:
            return statistics.mean(array)
        else: return None