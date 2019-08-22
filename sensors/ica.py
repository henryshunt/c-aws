import statistics
from datetime import datetime, timedelta

import RPi.GPIO as gpio

from sensors.sensor import Sensor
from sensors.sensor import LogType

# Inspeed Classic Anemometer
# self.start_time stores logging start time to ensure enough data exists to
# create a final value
# self.utc stores current time to use for final value calculation
class ICA(Sensor):

    def __init__(self):
        super().__init__()
        self.pause = True
        self.start_time = None
        self.utc = None

    def setup(self, pin):
        super().setup(LogType.ARRAY)
        self.address = pin
        
        gpio.setup(self.address, gpio.IN, pull_up_down=gpio.PUD_DOWN)
        gpio.add_event_detect(self.address, gpio.FALLING,
            callback=self.interrupt, bouncetime=1)

    def interrupt(self, channel):
        """ Runs whenever an interrupt is triggered from the sensor
        """
        if self.pause == True: return
        if self.primary == None: self.primary = []
        self.primary.append(datetime.utcnow())
        
    def prepare_secondary(self, utc):
        self.utc = utc
        ten_mins_ago = self.utc - timedelta(minutes=10)

        if self.secondary != None:
            for tick in list(self.secondary):
                if tick < ten_mins_ago: self.secondary.remove(tick)
            if len(self.secondary) == 0: self.secondary = None

    def shift(self):
        if self.primary != None:
            if self.secondary == None:
                self.secondary = self.primary[:]
            else: self.secondary.extend(self.primary)
            
    def array_format(self, array):
        ten_mins_ago = self.utc - timedelta(minutes=10)
        if not ten_mins_ago >= self.start_time: return None

        if array == None: return 0        
        values = []

        # Iterate over data in three second samples
        for second in range(0, 118, 3):
            start = ten_mins_ago + timedelta(seconds=second)
            end = start + timedelta(seconds=3)
            ticks_in_sample = 0

            # Calculate three second average wind speed
            for tick in array:
                if tick >= start and tick < end: ticks_in_sample += 1

            values.append((ticks_in_sample * 2.5) / 3)
        return statistics.mean(values)

    def get_secondary_gust(self):
        """ Calculates maximum 3 second wind gust over past 10 minutes for the
            secondary data store
        """
        ten_mins_ago = self.utc - timedelta(minutes=10)
        if not ten_mins_ago >= self.start_time: return None
        if self.secondary == None: return 0
        value = 0

        # Iterate over each second in three second samples
        for second in range(0, 598):
            start = ten_mins_ago + timedelta(seconds=second)
            end = start + timedelta(seconds=3)
            ticks_in_sample = 0

            # Calculate 3 second average wind speed, check if highest
            for tick in self.secondary:
                if tick >= start and tick < end: ticks_in_sample += 1

            sample = (ticks_in_sample * 2.5) / 3
            if sample > value: value = sample
        return value