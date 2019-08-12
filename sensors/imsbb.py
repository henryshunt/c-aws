import RPi.GPIO as gpio

from sensors.sensor import Sensor

# Instromet Mini Sun Board with binary output
class IMSBB(Sensor):  

    def setup(self, log_type, pin):
        super().setup(log_type)
        self.address = pin
        
        gpio.setup(self.address, gpio.IN, pull_up_down=gpio.PUD_DOWN)

    def read_value(self):
        return 1 if gpio.input(self.address) == True else 0

    def array_format(self, array):
        if array != None:
            return sum(array)
        else: return None