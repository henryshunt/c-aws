import statistics

from gpiozero import CPUTemperature

from sensors.sensor import Sensor

# CPU temperature sensor
class CPU(Sensor):

    def setup(self, log_type):
        super().setup(log_type)

    def read_value(self):
        return CPUTemperature().temperature

    def array_format(self, array):
        if array != None:
            return statistics.mean(array)
        else: return None