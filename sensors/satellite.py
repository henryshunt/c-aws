import time
import json

import serial
from serial.tools.list_ports import comports

from routines.helpers import SensorError

class Satellite():
    def __init__(self):
        self._device = None

    def open(self):
        for port in comports():
            if not port.name.startswith("ttyUSB"):
                continue

            device = serial.Serial(port="/dev/" + port.name, baudrate=115200)
            if device.isOpen:
                device.close()

            device.open()
            time.sleep(2) # Wait for the Arduino to reset after connecting
            response = self.command(device, "PING\n")

            # We use in because the first transmission from the device sometimes has
            # extra characters at the ends
            if response != None and "AWS Satellite Device" in response:
                response = self.command(device, "ID\n")

                if response != None and int(response) == 1:
                    cmd = "CONFIG { windSpeedEnabled:true,windSpeedPin:2,windDirectionEnabled:true,windDirectionPin:7}\n"
                    response = self.command(device, cmd)
                    
                    if response != None and response == "OK":
                        self._device = device
                        return
            
            device.close()

        if self._device == None:
            raise SensorError("Satellite not found")

    def start(self):
        response = self.command(self._device, "START\n")
        if response == None or response == "ERROR":
            raise SensorError("Error response while starting satellite")

    def sample(self):
        response = self.command(self._device, "SAMPLE\n")
        if response == None or response == "ERROR":
            raise SensorError("Error response while sampling satellite")

        sample = json.loads(response)
        return sample

    def command(self, device, command):
        device.write(command.encode("utf-8"))

        response = ""
        resp_ended = False
        start = time.perf_counter()

        while not resp_ended:
            if device.in_waiting > 0:
                char = device.read(1).decode("utf-8")

                if char != "\n":
                    response += char
                else: resp_ended = True

            if time.perf_counter() - start > 0.1:
                return None

        return response