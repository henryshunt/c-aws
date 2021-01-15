import time
from datetime import datetime, timezone
import busio
import board
import adafruit_ds3231
from RPi import GPIO as gpio


class Clock:
    def __init__(self, sqwPin):
        self.sqwPin = sqwPin
        self.rtc = None
        self.on_tick = None

    def open(self):
        self.rtc = adafruit_ds3231.DS3231(busio.I2C(board.SCL, board.SDA))
        self.rtc.alarm1_interrupt = False
        self.rtc.alarm1_status = False

    def get_time(self):
        time = self.rtc.datetime
        return datetime(time.tm_year, time.tm_mon, time.tm_mday, time.tm_hour,
            time.tm_min, time.tm_sec, tzinfo=timezone.utc)

    def start(self):
        gpio.setup(self.sqwPin, gpio.IN)
        gpio.add_event_detect(self.sqwPin, gpio.FALLING, callback=self._tick)

        self.rtc.alarm1 = (time.struct_time((0, 0, 0, 0, 0, 0, 0, 0, 0)), "secondly")
        self.rtc.alarm1_interrupt = True

    def _tick(self, channel):
        self.rtc.alarm1_status = False

        time = self.rtc.datetime
        time2 = datetime(time.tm_year, time.tm_mon, time.tm_mday, time.tm_hour,
            time.tm_min, time.tm_sec, tzinfo=timezone.utc)

        self.on_tick(time2)