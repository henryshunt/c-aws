import os
import statistics

from sensors.sensor import Sensor
from sensors.sensor import LogType

class DS18B20(Sensor):

    def __init__(self):
        super().__init__()
        self.error = False

    def setup(self, log_type, address):
        super().setup(log_type)
        self.address = address
        
        # Check a sensor with that address exists
        if not os.path.isdir("/sys/bus/w1/devices/" + address):
            raise Exception("Address does not exist")

    def sample(self):
        self.error = False

        try:
            value = self.read_value()

            if self.log_type == LogType.VALUE:
                self.primary = value

            elif self.log_type == LogType.ARRAY:
                if self.primary == None: self.primary = []
                self.primary.append(value)
        except: self.error = True

    def read_value(self):
        with open("/sys/bus/w1/devices/"
            + self.address + "/w1_slave", "r") as sensor:
            data = sensor.readlines()

            # Convert value to degrees C and check for error values
            temp = int(data[1][data[1].find("t=") + 2:]) / 1000
            if temp == -127 or temp == 85:
                raise Exception("Received sensor error code")
            return temp

    def array_format(self, array):
        if array != None:
            return statistics.mean(array)
        else: return None

    def reset_primary(self):
        super().reset_primary()
        self.error = False

    def reset_secondary(self):
        super().reset_secondary()
        self.error = False
