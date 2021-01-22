import RPi.GPIO as gpio

# Instromet Mini Sun Board, binary output
class IMSBB():  
    def __init__(self, pin):
        self._pin = pin

    def open(self):        
        gpio.setup(self.pin, gpio.IN, pull_up_down=gpio.PUD_DOWN)

    def sample(self):
        return 1 if gpio.input(self._pin) == True else 0