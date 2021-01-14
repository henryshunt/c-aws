import RPi.GPIO as gpio

from sensors.sensor import Sensor
from sensors.store import SampleStore

# Instromet Mini Sun Board, binary output
class IMSBB():  
    def __init__(self, pin):
        self._pin = pin
        self.store = SampleStore()

    def open(self):        
        gpio.setup(self.pin, gpio.IN, pull_up_down=gpio.PUD_DOWN)

    def sample(self):
        value = 1 if gpio.input(self._pin) == True else 0
        self.store.active_store.append(value)

    def get_total(self):
        return sum(self.store.inactive_store)