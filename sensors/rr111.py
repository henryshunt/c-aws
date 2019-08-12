import RPi.GPIO as gpio

from sensors.sensor import Sensor
from sensors.sensor import LogType

# Rainwise Rainew 111
class RR111(Sensor):

    def __init__(self):
        super().__init__()
        self.pause = True
    
    def setup(self, pin):
        super().setup(LogType.ARRAY)
        self.address = pin
        
        gpio.setup(self.address, gpio.IN, pull_up_down=gpio.PUD_DOWN)
        gpio.add_event_detect(self.address, gpio.FALLING,
            callback=self.interrupt, bouncetime=150)

    def interrupt(self, channel):
        if self.pause == True: return
        if self.primary == None: self.primary = []
        self.primary.append(1)

    def array_format(self, array):
        if array != None:
            return sum(array) * 0.254
        else: return 0