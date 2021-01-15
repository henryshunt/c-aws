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
from routines.helpers import SensorError
from routines.data import Report


class Sampler:
    def __init__(self):
        self._start_time = None
        self._air_temp = None
        self._rel_hum = None
        self._satellite = None
        self._wind_speed_10 = []
        self._wind_dir_10 = []
        self._sun_dur = None
        self._rainfall = None
        self._pressure = None

    def open(self):
        if config.sensors["air_temp"]["enabled"] == True:
            try:
                self._air_temp = MCP9808()
                self._air_temp.open()
            except Exception as e:
                helpers.log(None, "sampler", "Failed to open air_temp sensor")
                raise SensorError("Failed to open air_temp sensor", e)

        if config.sensors["rel_hum"]["enabled"] == True:
            try:
                self._rel_hum = HTU21D()
                self._rel_hum.open()
            except Exception as e:
                helpers.log(None, "sampler", "Failed to open rel_hum sensor")
                raise SensorError("Failed to open rel_hum sensor", e)

        if (config.sensors["satellite"]["wind_spd"]["enabled"] == True or
            config.sensors["satellite"]["wind_dir"]["enabled"] == True):
            try:
                self._satellite = Satellite()
                self._satellite.open()
            except Exception as e:
                helpers.log(None, "sampler", "Failed to open connection to satellite")
                raise SensorError("Failed to open connection to satellite", e)

        if config.sensors["sun_dur"]["enabled"] == True:
            try:
                self._sun_dur = IMSBB(config.sensors["sun_dur"]["pin"])
                self._sun_dur.open()
            except Exception as e:
                helpers.log(None, "sampler", "Failed to open sun_dur sensor")
                raise SensorError("Failed to open sun_dur sensor", e)

        if config.sensors["rain"]["enabled"] == True:
            try:
                self._rainfall = RR111(config.sensors["rain"]["pin"])
                self._rainfall.open()
            except Exception as e:
                helpers.log(None, "sampler", "Failed to open rain sensor")
                raise SensorError("Failed to open rain sensor", e)

        if config.sensors["pressure"]["enabled"] == True:
            try:
                self._pressure = BMP280()
                self._pressure.open()
            except Exception as e:
                helpers.log(None, "sampler", "Failed to open pressure sensor")
                raise SensorError("Failed to open pressure sensor", e)

        if config.sensors["camera"]["enabled"] == True:
            try:
                with picamera.PiCamera() as camera:
                    pass
            except Exception as e:
                helpers.log(None, "sampler", "Failed to open connection to camera")
                raise SensorError("Failed to open connection to camera", e)

    def start(self, time):
        self._start_time = time

        if (config.sensors["satellite"]["wind_spd"]["enabled"] == True or
            config.sensors["satellite"]["wind_dir"]["enabled"] == True):
            try:
                self._satellite.start()
            except Exception as e:
                helpers.log(None, "sampler", "Failed to start satellite")
                raise SensorError("Failed to start satellite", e)

        if config.sensors["rain"]["enabled"] == True:
            self._rainfall.pause = False

    def sample(self, time):
        if (config.sensors["satellite"]["wind_spd"]["enabled"] == True or
            config.sensors["satellite"]["wind_dir"]["enabled"] == True):
            try:
                self._satellite.sample(time)
            except Exception as e:
                helpers.log(time, "sampler", "Failed to sample satellite")
                raise SensorError("Failed to sample satellite", e)

        if config.sensors["air_temp"]["enabled"] == True:
            try:
                self._air_temp.sample()
            except:
                helpers.log(time, "sampler", "Failed to sample air_temp sensor")
                raise SensorError("Failed to sample air_temp sensor", e)

        if config.sensors["rel_hum"]["enabled"] == True:
            try:
                self._rel_hum.sample()
            except:
                helpers.log(time, "sampler", "Failed to sample rel_hum sensor")
                raise SensorError("Failed to sample rel_hum sensor", e)

        if config.sensors["sun_dur"]["enabled"] == True:
            try:
                self._sun_dur.sample()
            except:
                helpers.log(time, "sampler", "Failed to sample sun_dur sensor")
                raise SensorError("Failed to sample sun_dur sensor", e)

        if config.sensors["rain"]["enabled"] == True:
            try:
                self._rainfall.sample()
            except:
                helpers.log(time, "sampler", "Failed to sample rain sensor")
                raise SensorError("Failed to sample rain sensor", e)

        if config.sensors["pressure"]["enabled"] == True:
            try:
                self._pressure.sample()
            except:
                helpers.log(time, "sampler", "Failed to sample pressure sensor")
                raise SensorError("Failed to sample pressure sensor", e)

    def cache_samples(self):
        if config.sensors["air_temp"]["enabled"] == True:
            self._air_temp.store.switch_store()
        if config.sensors["rel_hum"]["enabled"] == True:
            self._rel_hum.store.switch_store()
        if (config.sensors["satellite"]["wind_spd"]["enabled"] == True or
            config.sensors["satellite"]["wind_dir"]["enabled"] == True):
            self._satellite.store.switch_store()
        if config.sensors["sun_dur"]["enabled"] == True:
            self._sun_dur.store.switch_store()
        if config.sensors["rain"]["enabled"] == True:
            self._rainfall.store.switch_store()
        if config.sensors["pressure"]["enabled"] == True:
            self._pressure.store.switch_store()

    def report(self, time):
        report = Report(time)

        if config.sensors["air_temp"]["enabled"] == True:
            report.air_temp = self._air_temp.get_average()
        if config.sensors["rel_hum"]["enabled"] == True:
            report.rel_hum = self._rel_hum.get_average()
        
        if (config.sensors["satellite"]["wind_spd"]["enabled"] == True or
            config.sensors["satellite"]["wind_dir"]["enabled"] == True):
            self.update_wind_stores(time)
            wind = self.calculate_wind_values(time)

        if config.sensors["sun_dur"]["enabled"] == True:
            report.sun_dur = self._sun_dur.get_total()
        if config.sensors["rain"]["enabled"] == True:
            report.rainfall = self._rainfall.get_total()
        if config.sensors["pressure"]["enabled"] == True:
            report.sta_pres = self._pressure.get_average()
        
        report.dew_point = data.calculate_DewP(report.air_temp, report.rel_hum)
        report.msl_pres = data.calculate_MSLP(report.sta_pres, report.air_temp)

        return report

    def update_wind_stores(self, time):
        ten_min_start = time - timedelta(minutes=10)

        for sample in self._satellite.store.inactive_store:
            self._wind_speed_10.append((sample[0], sample[1]["windSpeed"] * 0.31))
            self._wind_dir_10.append(sample[1]["windDirection"])

    def calculate_wind_values(self, ten_minute_end):
        return self.tuple_average(self._wind_speed_10, 1)

    def tuple_average(self, listt, column):
        total = 0
        count = 0

        for i in listt:
            total += i[column]
            count += 1
        
        return total / count

    def camera_report(self, time):
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