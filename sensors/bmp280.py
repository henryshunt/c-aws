import statistics

import board
import busio
import adafruit_bmp280

from sensors.store import SampleStore

class BMP280():
    def __init__(self):
        self._device = None
        self.store = SampleStore()

    def open(self):
        self._device = adafruit_bmp280.Adafruit_BMP280_I2C(
            busio.I2C(board.SCL, board.SDA))

    def sample(self):
        self.store.active_store.append(self._device.pressure)

    def get_average(self):
        if len(self.store.inactive_store) != 0:
            return statistics.mean(self.store.inactive_store)
        else: return None