import os
from datetime import datetime, timedelta
import time
from threading import Thread
import string
import random

import daemon
import RPi.GPIO as gpio
import picamera

import routines.config as config
import routines.helpers as helpers
from sensors.sensor import LogType
from sensors.mcp9808 import MCP9808
from sensors.htu21d import HTU21D
from sensors.ica import ICA
from sensors.iev2 import IEV2
from sensors.imsbb import IMSBB
from sensors.rr111 import RR111
from sensors.bmp280 import BMP280
import routines.data as data


class Sampler:
    def __init__(self):
        self.air_temp = None
        self.rel_hum = None
        self.WSpd_sensor = ICA()
        self.WDir_sensor = IEV2()
        self.sun_dur = None
        self.rain = None
        self.pressure = None
        self.start_time = None

    def open(self):
        if config.sensors["air_temp"]["enabled"] == True:
            try:
                self.air_temp = MCP9808()
                self.air_temp.open()
            except:
                helpers.log(None, "sampler", "Failed to open air_temp sensor.")
                return False

        if config.sensors["rel_hum"]["enabled"] == True:
            try:
                self.rel_hum = HTU21D()
                self.rel_hum.open()
            except:
                helpers.log(None, "sampler", "Failed to open rel_hum sensor.")
                return False

        # if config.sensors["wind_spd"]["enabled"] == True:
        #     try:
        #         self.WSpd_sensor.setup(config.WSpd_pin)
        #     except: helpers.data_error("__main__() 3")

        # if config.sensors["wind_dir"]["enabled"] == True:
        #     try:
        #         self.WDir_sensor.setup(config.WDir_channel, config.WDir_offset)
        #     except: helpers.data_error("__main__() 4")

        if config.sensors["sun_dur"]["enabled"] == True:
            try:
                self.sun_dur = IMSBB(config.sensors["sun_dur"]["pin"])
                self.sun_dur.open()
            except:
                helpers.log(None, "sampler", "Failed to open sun_dur sensor.")
                return False

        if config.sensors["rain"]["enabled"] == True:
            try:
                self.rain = RR111(config.sensors["rain"]["pin"])
                self.rain.open()
            except:
                helpers.log(None, "sampler", "Failed to open rain sensor.")
                return False

        if config.sensors["pressure"]["enabled"] == True:
            try:
                self.pressure = BMP280()
                self.pressure.open()
            except:
                helpers.log(None, "sampler", "Failed to open pressure sensor.")
                return False

        if config.camera_logging == True:
            try:
                with picamera.PiCamera() as camera: pass
            except: helpers.data_error("__main__() 13")

        return True

    def start(self, time):
        self.start_time = time
        self.WSpd_sensor.pause = False

        if config.sensors["rain"]["enabled"] == True:
            self.rain.pause = False

        return True

    def sample(self, time):
        """ Triggered every second to read sensor values into a list for averaging
        """
        if config.sensors["air_temp"]["enabled"] == True:
            try:
                self.air_temp.sample()
            except:
                helpers.log(time, "sampler", "Failed to sample air_temp sensor.")
                return False

        if config.sensors["rel_hum"]["enabled"] == True:
            try:
                self.rel_hum.sample()
            except:
                helpers.log(time, "sampler", "Failed to sample rel_hum sensor.")
                return False

        # if config.WDir == True:
        #     try:
        #         self.WDir_sensor.sample(time)
        #     except: helpers.data_error("schedule_second() 3")

        if config.sensors["sun_dur"]["enabled"] == True:
            try:
                self.sun_dur.sample()
            except:
                helpers.log(time, "sampler", "Failed to sample sun_dur sensor.")
                return False

        if config.sensors["rain"]["enabled"] == True:
            try:
                self.rain.sample()
            except:
                helpers.log(time, "sampler", "Failed to sample rain sensor.")
                return False

        if config.sensors["pressure"]["enabled"] == True:
            try:
                self.pressure.sample()
            except:
                helpers.log(time, "sampler", "Failed to sample pressure sensor.")
                return False

        return True

    def report(self, time):
        """ Reads all sensors, calculates derived and averaged parameters, and
            saves the data to the database
        """
        report = data.ReportFrame(time)

        if config.sensors["air_temp"]["enabled"] == True:
            self.air_temp.store.switch_store()
            report.air_temperature = self.air_temp.get_average()

        if config.sensors["rel_hum"]["enabled"] == True:
            self.rel_hum.store.switch_store()
            report.relative_humidity = self.rel_hum.get_average()
        
        # if config.WSpd == True:
        #     WSpd_sensor.prepare_secondary(time)
        #     WSpd_value = WSpd_sensor.get_secondary()

        #     if WSpd_value != None:
        #         report.wind_speed = round(WSpd_value, 2)

        #     # Derive wind gust
        #     WGst_value = WSpd_sensor.get_secondary_gust()
        #     if WGst_value != None:
        #         report.wind_gust = round(WGst_value, 2)

        # if config.WDir == True:
        #     WDir_sensor.prepare_secondary(time)
        #     WDir_value = WDir_sensor.get_secondary()

        #     if WDir_value != None:
        #         WDir_value = int(round(WDir_value, 0))
        #         if WDir_value == 360: WDir_value = 0
        #         report.wind_direction = WDir_value

        if config.sensors["sun_dur"]["enabled"] == True:
            self.sun_dur.store.switch_store()
            report.sunshine_duration = self.sun_dur.get_total()

        if config.sensors["rain"]["enabled"] == True:
            self.rain.store.switch_store()
            report.rainfall = self.rain.get_total()

        if config.sensors["pressure"]["enabled"] == True:
            self.pressure.store.switch_store()
            report.station_pressure = self.pressure.get_average()
        
        report.dew_point = data.calculate_DewP(
            report.air_temperature, report.relative_humidity)

        report.mean_sea_level_pressure = data.calculate_MSLP(
            report.station_pressure, report.air_temperature)

        print(report.air_temperature)
        print(report.rainfall)
        return report


def operation_log_camera(utc):
    """ Takes an image on the camera if it is currently a five minute interval
        of the hour, and saves it to the camera drive
    """
    utc_minute = str(utc.minute)
    if not utc_minute.endswith("0") and not utc_minute.endswith("5"):
        return

    # Only take images between sunrise and sunset
    sun_times = helpers.solar_times(helpers.utc_to_local(utc))    
    sunset_threshold = sun_times[0] + timedelta(minutes=60)
    sunrise_threshold = sun_times[0] - timedelta(minutes=60)
    if utc < sunrise_threshold or utc > sunset_threshold: return

    # Check the filesystem
    try:
        if (not os.path.isdir(config.camera_directory) or 
            not os.path.ismount(config.camera_directory)):
            helpers.data_error("operation_log_camera() 0")
            return

    except:
        helpers.data_error("operation_log_camera() 1")
        return

    free_space = helpers.remaining_space(config.camera_directory)
    if free_space == None or free_space < 0.1:
        helpers.data_error("operation_log_camera() 2")
        return


    try:
        image_dir = os.path.join(config.camera_directory, 
            utc.strftime("%Y/%m/%d"))
        if not os.path.isdir(image_dir): os.makedirs(image_dir)
        image_name = utc.strftime("%Y-%m-%dT%H-%M-%S")
    
        # Set image resolution, wait for auto settings, then capture
        with picamera.PiCamera() as camera:
            camera.resolution = (1280, 960)
            time.sleep(2.5)
            camera.capture(os.path.join(image_dir, image_name + ".jpg"))

        # Write data to upload database
        if config.camera_uploading == True:
            values = (utc.strftime("%Y-%m-%d %H:%M:%S"),)
            query = data.query_database(config.upload_db_path,
                "INSERT INTO camReports VALUES (?)", values)

            if query == False:
                helpers.data_error("operation_log_camera() 4")
    except: helpers.data_error("operation_log_camera() 3")