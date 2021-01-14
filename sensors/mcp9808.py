import statistics

import board
import busio
import adafruit_mcp9808

from sensors.sensor import Sensor
from sensors.store import SampleStore

class MCP9808():
    def __init__(self):
        self.device = None
        self.store = SampleStore()

    def open(self):
        self.device = adafruit_mcp9808.MCP9808(busio.I2C(board.SCL, board.SDA))

    def sample(self):
        self.store.active_store.append(self.device.temperature)

    def get_average(self):
        if len(self.store.inactive_store) != 0:
            return statistics.mean(self.store.inactive_store)
        else: return None