import statistics

import board
import busio
import adafruit_htu21d

from sensors.sensor import Sensor
from sensors.store import SampleStore

class HTU21D():
    def __init__(self):
        self._device = None
        self.store = SampleStore()

    def open(self):
        self._device = adafruit_htu21d.HTU21D(busio.I2C(board.SCL, board.SDA))

    def sample(self):
        value = self._device.relative_humidity

        if value > 100:
            value = 100
        elif value < 0:
            value = 0

        self.store.active_store.append(value)

    def get_average(self):
        if len(self.store.inactive_store) != 0:
            return statistics.mean(self.store.inactive_store)
        else: return None