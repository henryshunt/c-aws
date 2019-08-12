import statistics

import board
import busio
import adafruit_mcp9808

from sensors.sensor import Sensor

class MCP9808(Sensor):

    def setup(self, log_type):
        super().setup(log_type)

        i2c = busio.I2C(board.SCL, board.SDA)
        self.bridge = adafruit_mcp9808.MCP9808(i2c)

    def read_value(self):
        return self.bridge.temperature

    def array_format(self, array):
        if array != None:
            return statistics.mean(array)
        else: return None