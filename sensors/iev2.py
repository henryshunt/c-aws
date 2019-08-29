from datetime import timedelta

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
        self.offset = None
        self.start_time = None
        self.utc = None

    def setup(self, adc_channel, offset):
        super().setup(LogType.ARRAY)
        self.address = adc_channel
        self.offset = offset
        
        spi = busio.SPI(clock=board.SCK, MISO=board.MISO, MOSI=board.MOSI)
        mcp3008_a = mcp3008.MCP3008(spi, digitalio.DigitalInOut(board.D8))
        self.bridge = AnalogIn(mcp3008_a, adc_channel)

    def sample(self, timestamp):
        value = self.read_value()
        if self.primary == None: self.primary = []
        self.primary.append((timestamp, value))

    def shift(self):
        if self.primary != None:
            if self.secondary == None:
                self.secondary = self.primary[:]
            else: self.secondary.extend(self.primary)

    def read_value(self):
        adc_voltage = self.bridge.voltage
        if adc_voltage < 0.165: adc_voltage = 0.165
        elif adc_voltage > 3.135: adc_voltage = 3.135

        degrees = (adc_voltage - 0.165) / (3.135 - 0.165) * (360 - 0)

        # Modify value to account for non-zero-degrees at north
        if self.offset != None:
            degrees += self.offset
            if degrees >= 360: degrees -= 360
            elif degrees < 0: degrees += 360

        if degrees == 360: degrees = 0
        return degrees

    def prepare_secondary(self, utc):
        """ Prepares the secondary data store for reading a final value
        """
        self.utc = utc
        ten_mins_ago = self.utc - timedelta(minutes=10)

        if self.secondary != None:
            for sample in list(self.secondary):
                if sample[0] < ten_mins_ago: self.secondary.remove(sample)
            if len(self.secondary) == 0: self.secondary = None
            
    def array_format(self, array):
        ten_mins_ago = self.utc - timedelta(minutes=10)
        if not ten_mins_ago >= self.start_time: return None
        if array == None: return None

        total = 0
        for sample in array: total += sample[1]
        average = total / len(array)        
        if average == 360: average = 0
        return average