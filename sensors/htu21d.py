import board
import busio
import adafruit_htu21d

class HTU21D():
    def __init__(self):
        self._device = None

    def open(self):
        self._device = adafruit_htu21d.HTU21D(busio.I2C(board.SCL, board.SDA))

    def sample(self):
        value = self._device.relative_humidity

        if value > 100:
            value = 100
        elif value < 0:
            value = 0

        return value