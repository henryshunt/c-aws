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
from sensors.mcp9808 import MCP9808
from sensors.htu21d import HTU21D
from sensors.ica import ICA
from sensors.iev2 import IEV2
from sensors.imsbb import IMSBB
from sensors.rr111 import RR111
from sensors.bmp280 import BMP280
from sensors.satellite import Satellite
import routines.data as data
from sensors.store import SampleStore


class Sampler:
    def __init__(self):
        self.air_temp = None
        self.rel_hum = None
        self.satellite = None
        self.wind_spd_10 = []
        self.wind_dir_10 = []
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

        if (config.sensors["satellite"]["wind_spd"]["enabled"] == True or
            config.sensors["satellite"]["wind_dir"]["enabled"] == True):
            
            self.satellite = Satellite()
            self.satellite.open()

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
        self.satellite.start()

        if config.sensors["rain"]["enabled"] == True:
            self.rain.pause = False

        return True

    def sample(self, time):
        """ Triggered every second to read sensor values into a list for averaging
        """
        # if (config.sensors["satellite"]["wind_spd"]["enabled"] == True or
        #     config.sensors["satellite"]["wind_dir"]["enabled"] == True):
        self.satellite.sample(time)

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
        
        if (config.sensors["satellite"]["wind_spd"]["enabled"] == True or
            config.sensors["satellite"]["wind_dir"]["enabled"] == True):

            self.satellite.store.switch_store()
            self.update_wind_stores(time)
            wind = self.calculate_wind_values(time)
            print(wind)

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

    def update_wind_stores(self, time):
        ten_min_start = time - timedelta(minutes=10)

        for sample in self.satellite.store.inactive_store:
            self.wind_spd_10.append((sample[0], sample[1]["windSpeed"] * 0.31))
            self.wind_dir_10.append(sample[1]["windDirection"])

    def calculate_wind_values(self, ten_minute_end):
        return self.tuple_average(self.wind_spd_10, 1)

    def tuple_average(self, listt, column):
        total = 0
        count = 0

        for i in listt:
            total += i[column]
            count += 1
        
        return total / count


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