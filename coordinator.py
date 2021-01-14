import os
from datetime import datetime, timezone
from RPi import GPIO as gpio
import time

from routines import config
from routines import helpers
from sampler import Sampler
#from aws_support import AWSSupport
from clock import Clock

import busio
import adafruit_ds3231
import board


class Coordinator():
    def __init__(self):
        self.clock = None
        self.sampler = None
        self.subsys_support = None
        self.sampling = False

    def startup(self):
        helpers.log(None, "main", "Startup.")

        if config.load() == False:
            helpers.log(None, "main", "Failed to load configuration.")
            return

        gpio.setwarnings(False)
        gpio.setmode(gpio.BCM)

        gpio.setup(config.data_led_pin, gpio.OUT)
        gpio.output(config.data_led_pin, gpio.LOW)
        gpio.setup(config.error_led_pin, gpio.OUT)
        gpio.output(config.error_led_pin, gpio.LOW)

        self.clock = Clock(14)
        self.clock.open()
        self.clock.on_tick = self.on_clock_tick

        helpers.log(self.clock.get_time(), "main", "Opened connection to clock.")

        if not self.file_system():
            gpio.output(config.error_led_pin, gpio.HIGH)
            return

        # self.camera()

        self.sampler = Sampler()
        
        if not self.sampler.open():
            gpio.output(config.error_led_pin, gpio.HIGH)
            return

        time.sleep(1)
        gpio.output(config.data_led_pin, gpio.HIGH)
        gpio.output(config.error_led_pin, gpio.HIGH)
        time.sleep(2.5)
        gpio.output(config.data_led_pin, gpio.LOW)
        gpio.output(config.error_led_pin, gpio.LOW)

        helpers.log(self.clock.get_time(), "main", "Starting clock.")
        self.clock.start()

    def file_system(self):
        free_space = helpers.remaining_space(config.data_directory)

        if free_space == None or free_space < 0.1:
            helpers.log(self.clock.get_time(), "main", "Not enough free space.")
            return False

        try:
            if not os.path.isdir(config.data_directory):
                os.makedirs(config.data_directory)
        except:
            helpers.log(self.clock.get_time(), "main", "Failed to create directory.")
            return False

        helpers.log(self.clock.get_time(),
            "main", "Free space: " + str(round(free_space, 2)) + " GB.")

        try:
            if not os.path.isfile(config.main_db_path):
                data.create_database(config.main_db_path)
                helpers.log(self.clock.get_time(), "main", "Created main database.")
        except:
            helpers.log(self.clock.get_time(), "main", "Failed to create main database.")
            return False

        if (config.report_uploading == True or
            config.envReport_uploading == True or
            config.camera_uploading == True or
            config.dayStat_uploading == True):

            try:
                if not os.path.isfile(config.upload_db_path):
                    data.create_database(config.upload_db_path)
                    helpers.log(self.clock.get_time(), "main", "Created transmit database.")
            except:
                helpers.log(self.clock.get_time(), 
                    "main", "Failed to create transmit database.")
                return False

        return True

    def camera(self):
        # Check camera storage drive is ready for use
        if config.camera_logging == True:
            try:
                if not os.path.isdir(config.camera_directory):
                    raise Exception("Directory does not exist")
            except: helpers.init_error(5, True, True)

            try:
                if not os.path.ismount(config.camera_directory):
                    raise Exception("Directory not a mount point")
            except: helpers.init_error(6, True, True)

            free_space = helpers.remaining_space(config.camera_directory)
            if free_space == None or free_space < 0.1:
                helpers.init_error(7, True, True)
    
    def on_clock_tick(self, time):
        if not self.sampling:
            if time.second == 0:
                if self.sampler.start(time):
                    self.sampling = True
                    helpers.log(self.clock.get_time(), "main", "Started sampling.")
                else:
                    helpers.log(self.clock.get_time(), "main", "Failed to start sampling.")
                    gpio.output(config.error_led_pin, gpio.HIGH)
            return

        if not self.sampler.sample(time):
            gpio.output(config.error_led_pin, gpio.HIGH)

        if time.second == 0:
            self.sampler.report(time)
            print("report")
            # new Thread(() =>
            # {
            #     LogReport(e.Time);
            #     // Transmitter.Transmit();
            # }).Start()

    # def log_report(time):
    #     Stopwatch ledStopwatch = new Stopwatch()
    #     ledStopwatch.Start()

    #     gpio.Write(config.dataLedPin, PinValue.High)

    #     Report report = sampler.Report(time)
    #     Database.WriteReport(report)

    #     # Ensure the data LED stays on for at least 1.5 seconds
    #     ledStopwatch.Stop()
    #     if (ledStopwatch.ElapsedMilliseconds < 1500)
    #         Thread.Sleep(1500 - (int)ledStopwatch.ElapsedMilliseconds)

    #     gpio.Write(config.dataLedPin, PinValue.Low)