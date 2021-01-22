import board
import busio
import adafruit_mcp9808

class MCP9808():
    def __init__(self):
        self._device = None

    def open(self):
        self._device = adafruit_mcp9808.MCP9808(busio.I2C(board.SCL, board.SDA))

    def sample(self):
        return self._device.temperature