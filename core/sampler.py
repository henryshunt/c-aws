import os
from datetime import datetime, timedelta
import time
from threading import Thread
import string
import random
import statistics

import daemon
import RPi.GPIO as gpio
import picamera

import routines.config as config
import routines.helpers as helpers
from sensors.mcp9808 import MCP9808
from sensors.htu21d import HTU21D
from sensors.ica import ICA
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
            self._update_wind_stores(time)

            if time - timedelta(minutes=10) >= self._start_time:
                wind = self._calc_wind_values(time)
                report.wind_speed = wind[0]
                report.wind_gust = wind[1]
                report.wind_dir = wind[2]

        if config.sensors["sun_dur"]["enabled"] == True:
            report.sun_dur = self._sun_dur.get_total()
        if config.sensors["rain"]["enabled"] == True:
            report.rainfall = self._rainfall.get_total()
        if config.sensors["pressure"]["enabled"] == True:
            report.sta_pres = self._pressure.get_average()
        
        report.dew_point = data.dew_point(report.air_temp, report.rel_hum)
        report.msl_pres = data.mslp(report.sta_pres, report.air_temp)
        return report

    def _update_wind_stores(self, ten_min_end):
        ten_min_start = ten_min_end - timedelta(minutes=10)

        if config.sensors["satellite"]["wind_spd"]["enabled"] == True:
            for sample in self._satellite.store.inactive_store:
                self._wind_speed_10.append(
                    (sample["time"], sample["windSpeed"] * ICA.WIND_SPEED_MPH_PER_HZ))

            # Remove samples older than 10 minutes
            new_speed_10 = []
            for sample in self._wind_speed_10:
                if sample[0] > ten_min_start:
                    new_speed_10.append(sample)
            self._wind_speed_10 = new_speed_10

        if config.sensors["satellite"]["wind_dir"]["enabled"] == True:
            for sample in self._satellite.store.inactive_store:
                self._wind_dir_10.append((sample["time"], sample["windDirection"]))

            # Remove samples older than 10 minutes
            new_dir_10 = []
            for sample in self._wind_dir_10:
                if sample[0] > ten_min_start:
                    new_dir_10.append(sample)
            self._wind_dir_10 = new_dir_10

    def _calc_wind_values(self, ten_min_end):
        speed = None
        gust = None
        direction = None

        if (config.sensors["satellite"]["wind_spd"]["enabled"] == True and
            len(self._wind_speed_10) > 0):
            speed = helpers.tuple_average(self._wind_speed_10, 1)
            gust = 0

            # Find the highest 3-second average in the previous 10 minutes. A
            # 3-second average includes the samples <= second T and > second T-3
            i = ten_min_end - timedelta(minutes=10)
            while i <= ten_min_end - timedelta(seconds=3):
                samples = []
                for sample in self._wind_speed_10:
                    if sample[0] > i and sample[0] <= i + timedelta(seconds=3):
                        samples.append(sample[1])

                if len(samples) > 0:
                    sample = statistics.mean(samples)
                    if sample > gust:
                        gust = sample

                i += timedelta(seconds=1)

            if (config.sensors["satellite"]["wind_dir"]["enabled"] == True and
                len(self._wind_dir_10) > 0 and speed > 0):
                vectors = []
                
                # Create a vector (speed and direction pair) for each second in
                # the previous 10 minutes
                i = ten_min_end - timedelta(seconds=599)
                while i <= ten_min_end:
                    s = next((x[1] for x in self._wind_speed_10 if x[0] == i), None)
                    d = next((x[1] for x in self._wind_dir_10 if x[0] == i), None)

                    if s != None and d != None:
                        vectors.append((s, d))

                    i += timedelta(seconds=1)

                if len(vectors) > 0:
                    direction = helpers.vector_average(vectors)

        return (speed, gust, direction)

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