import board
import busio
import adafruit_bmp280

class BMP280():
    def __init__(self):
        self._device = None

    def open(self):
        self._device = adafruit_bmp280.Adafruit_BMP280_I2C(
            busio.I2C(board.SCL, board.SDA))

    def sample(self):
        return self._device.pressure