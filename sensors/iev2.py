import statistics
from datetime import datetime, timedelta

import busio
import digitalio
import board
import adafruit_mcp3xxx.mcp3008 as mcp3008
from adafruit_mcp3xxx.analog_in import AnalogIn

from sensors.sensor import Sensor
from sensors.sensor import LogType

# Inspeed E-Vane II
# Requires sensor be connected to MCP3008 ADC
# self.start_time stores logging start time to ensure enough data exists to
# create a final value
# self.utc stores current time to use for final value calculation
class IEV2(Sensor):

    def __init__(self):
        super().__init__()
        self.start_time = None
        self.utc = None

    def setup(self, adc_channel):
        super().setup(LogType.ARRAY)
        self.address = adc_channel
        
        spi = busio.SPI(clock=board.SCK, MISO=board.MISO, MOSI=board.MOSI)
        mcp3008 = mcp3008.MCP3008(spi, digitalio.DigitalInOut(board.D5))
        self.bridge = AnalogIn(mcp3008, mcp3008.MCP["P" + str(adc_channel)])

    def sample(self, timestamp):
        """ Samples the sensor and stores the value in the primary data store
            along with a specified timestamp
        """
        value = self.read_value()
        if self.primary == None: self.primary = []
        self.primary.append((timestamp, value))

    def shift(self):
        """ Shifts the primary data store into the secondary data store
        """
        if self.primary != None:
            if self.secondary == None:
                self.secondary = self.primary[:]
            else: self.secondary.extend(self.primary)

    def read_value(self):
        adc_value = self.bridge.value

        if adc_value >= 52 and adc_value <= 976:
            degrees = (adc_value - 52) / (976 - 52) * (360 - 0)

            # Modify value to account for non-zero-degrees at north
            degrees -= 148
            if degrees >= 360: degrees -= 360
            elif degrees < 0: degrees += 360

            if degrees >= 359.5: degrees = 0
            return degrees
        else: raise Exception()

    def prepare_store(self, utc):
        """ Prepares the secondary data store for reading a final value
        """
        self.utc = utc
        two_mins_ago = self.utc - timedelta(minutes=2)

        if self.secondary != None:
            for sample in list(self.secondary):
                if sample[0] < two_mins_ago: self.secondary.remove(sample)
            if len(self.secondary) == 0: self.secondary = None
            
    def array_format(self, array):
        two_mins_ago = self.utc - timedelta(minutes=2)
        if not two_mins_ago >= self.start_time: return None
        if array == None: return None

        total = 0
        for sample in array: total += sample[1]
        average = total / len(array)

        if average >= 359.5: average = 0
        return average