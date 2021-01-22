import RPi.GPIO as gpio

# Rainwise Rainew 111
class RR111():
    def __init__(self, pin):
        self._pin = pin
        self._counter = 0
        self.pause = True

    def open(self):
        gpio.setup(self._pin, gpio.IN, pull_up_down=gpio.PUD_UP)
        gpio.add_event_detect(self._pin,
            gpio.FALLING, callback=self.on_interrupt, bouncetime=150)

    def sample(self):
        value = self._counter * 0.254
        self._counter = 0
        return value

    def on_interrupt(self, channel):
        self._counter += 1