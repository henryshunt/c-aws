import statistics

import board
import busio
import adafruit_bme280

from sensors.sensor import Sensor

class BME280(Sensor):

    def setup(self, log_type):
        super().setup(log_type)

        i2c = busio.I2C(board.SCL, board.SDA)
        self.bridge = adafruit_bme280.Adafruit_BME280_I2C(i2c)

    def read_value(self):
        return self.bridge.pressure

    def array_format(self, array):
        if array != None:
            return statistics.mean(array)
        else: return None