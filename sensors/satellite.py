import time
import json

import serial
from serial.tools.list_ports import comports

from sensors.store import SampleStore

class Satellite():
    def __init__(self):
        self._device = None
        self.store = SampleStore()

    def open(self):
        for port in comports():
            if not port.name.startswith("ttyUSB"):
                continue

            self._device = serial.Serial(port="/dev/" + port.name, baudrate=115200)

            if self._device.isOpen:
                self._device.close()

            self._device.open()

            time.sleep(2) # Wait for the Arduino to reset after connecting
            response = self.command("PING\n")

            # We use in because the first transmission from the device sometimes has
            # extra characters at the ends
            if "AWS Satellite Device" in response:
                response = self.command("ID\n")

                if int(response) == 1:
                    cmd = "CONFIG { windSpeedEnabled:true,windSpeedPin:2,windDirectionEnabled:true,windDirectionPin:7}\n"
                    
                    if self.command(cmd) == "OK":
                        return
            
            self._device.close()

    def start(self):
        self.command("START\n")

    def sample(self, time):
        self.store.active_store.append(
            (time, json.loads(self.command("SAMPLE\n"))))

    def command(self, command):
        self._device.write(command.encode("utf-8"))

        response = ""
        responseEnded = False

        while not responseEnded:
            if self._device.in_waiting > 0:
                readChar = self._device.read(1).decode("utf-8")

                if readChar != "\n":
                    response += readChar
                else: responseEnded = True

        return response