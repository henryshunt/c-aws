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
from sensors.ds18b20 import DS18B20
from sensors.htu21d import HTU21D
from sensors.ica import ICA
from sensors.iev2 import IEV2
from sensors.imsbb import IMSBB
from sensors.rr111 import RR111
from sensors.bmp280 import BMP280
from sensors.cpu import CPU
import routines.data as data


class Sampler:
    def __init__(self):
        self.air_temp = None
        self.rel_hum = None
        self.WSpd_sensor = ICA()
        self.WDir_sensor = IEV2()
        self.sun_dur = None
        self.rain = None
        self.sta_pres = None
        self.EncT_sensor = DS18B20()
        self.CPUT_sensor = CPU()
        self.start_time = None

    def open(self):
        if config.AirT == True:
            try:
                self.air_temp = MCP9808()
                self.air_temp.open()
            except:
                helpers.log(None, "sampler", "Failed to open air_temp sensor.")
                return False

        if config.RelH == True:
            try:
                self.rel_hum = HTU21D()
                self.rel_hum.open()
            except:
                helpers.log(None, "sampler", "Failed to open rel_hum sensor.")
                return False

        if config.WSpd == True:
            try:
                self.WSpd_sensor.setup(config.WSpd_pin)
            except: helpers.data_error("__main__() 3")

        if config.WDir == True:
            try:
                self.WDir_sensor.setup(config.WDir_channel, config.WDir_offset)
            except: helpers.data_error("__main__() 4")

        if config.SunD == True:
            try:
                self.sun_dur = IMSBB(config.SunD_pin)
                self.sun_dur.open()
            except:
                helpers.log(None, "sampler", "Failed to open sun_dur sensor.")
                return False

        if config.Rain == True:
            try:
                self.rain = RR111(config.Rain_pin)
                self.rain.open()
            except:
                helpers.log(None, "sampler", "Failed to open rain sensor.")
                return False

        if config.StaP == True:
            try:
                self.sta_pres = BMP280()
                self.sta_pres.open()
            except:
                helpers.log(None, "sampler", "Failed to open sta_pres sensor.")
                return False

        if config.envReport_logging == True:
            try:
                self.CPUT_sensor.setup(LogType.ARRAY)
            except: helpers.data_error("__main__() 11")

        if config.EncT == True:
            try:
                self.EncT_sensor.setup(LogType.VALUE, config.EncT_address)
            except: helpers.data_error("__main__() 12")

        if config.camera_logging == True:
            try:
                with picamera.PiCamera() as camera: pass
            except: helpers.data_error("__main__() 13")

        return True

    def start(self, time):
        self.start_time = time
        self.WSpd_sensor.pause = False

        if config.Rain == True:
            self.rain.pause = False

        return True

    def sample(self, time):
        """ Triggered every second to read sensor values into a list for averaging
        """
        if config.AirT == True:
            try:
                self.air_temp.sample()
            except:
                helpers.log(time, "sampler", "Failed to sample air_temp sensor.")
                return False

        if config.RelH == True:
            try:
                self.rel_hum.sample()
            except:
                helpers.log(time, "sampler", "Failed to sample rel_hum sensor.")
                return False

        if config.WDir == True:
            try:
                self.WDir_sensor.sample(time)
            except: helpers.data_error("schedule_second() 3")

        if config.SunD == True:
            try:
                self.sun_dur.sample()
            except:
                helpers.log(time, "sampler", "Failed to sample sun_dur sensor.")
                return False

        if config.Rain == True:
            try:
                self.rain.sample()
            except:
                helpers.log(time, "sampler", "Failed to sample rain sensor.")
                return False

        if config.StaP == True:
            try:
                self.sta_pres.sample()
            except:
                helpers.log(time, "sampler", "Failed to sample sta_pres sensor.")
                return False

        return True

    def report(self, time):
        """ Reads all sensors, calculates derived and averaged parameters, and
            saves the data to the database
        """
        frame = data.ReportFrame(time)

        # Shift and reset sensor stores to allow data collection to continue
        if config.AirT == True:
            self.air_temp.store.switch_store()
        if config.RelH == True:
            self.rel_hum.store.switch_store()
        if config.WSpd == True:
            self.WSpd_sensor.shift()
            self.WSpd_sensor.reset_primary()
        if config.WDir == True:
            self.WDir_sensor.shift()
            self.WDir_sensor.reset_primary()
        if config.SunD == True:
            self.sun_dur.store.switch_store()
        if config.Rain == True:
            self.rain.store.switch_store()
        if config.StaP == True:
            self.sta_pres.store.switch_store()

        if config.WSpd == True: self.WSpd_sensor.pause = False

        # Process air temperature
        if config.AirT == True:
            value = self.air_temp.get_average()

            if value != None:
                frame.air_temperature = round(value, 2)

        # Process relative humidity
        if config.RelH == True:
            value = self.rel_hum.get_average()

            if value != None:
                frame.relative_humidity = round(value, 2)
        
        # Process wind speed
        if config.WSpd == True:
            WSpd_sensor.prepare_secondary(time)
            WSpd_value = WSpd_sensor.get_secondary()

            if WSpd_value != None:
                frame.wind_speed = round(WSpd_value, 2)

            # Derive wind gust
            WGst_value = WSpd_sensor.get_secondary_gust()
            if WGst_value != None:
                frame.wind_gust = round(WGst_value, 2)

        # Process wind direction
        if config.WDir == True:
            WDir_sensor.prepare_secondary(time)
            WDir_value = WDir_sensor.get_secondary()

            if WDir_value != None:
                WDir_value = int(round(WDir_value, 0))
                if WDir_value == 360: WDir_value = 0
                frame.wind_direction = WDir_value

        # Process sunshine duration
        if config.SunD == True:
            value = self.sun_dur.get_total()

            if value != None:
                frame.sunshine_duration = value

        # Process rainfall
        if config.Rain == True:
            value = self.rain.get_total()

            if value != None:
                frame.rainfall = round(value, 3)

        # Process station pressure
        if config.StaP == True:
            value = self.sta_pres.get_average()

            if value != None:
                frame.station_pressure = round(value, 2)
        
        # Derive dew point
        DewP_value = data.calculate_DewP(frame.air_temperature,
            frame.relative_humidity)

        if DewP_value != None:
            frame.dew_point = round(DewP_value, 2)

        # Derive mean sea level pressure
        MSLP_value = data.calculate_MSLP(frame.station_pressure,
            frame.air_temperature)

        if MSLP_value != None:
            frame.mean_sea_level_pressure = round(MSLP_value, 2)


        # Write data to database
        QUERY = ("INSERT INTO reports VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, "
                + "?, ?, ?, ?)")
        values = (frame.time.strftime("%Y-%m-%d %H:%M:%S"), frame.air_temperature,
            frame.exposed_temperature, frame.relative_humidity, frame.dew_point,
            frame.wind_speed, frame.wind_direction, frame.wind_gust, 
            frame.sunshine_duration, frame.rainfall, frame.station_pressure,
            frame.mean_sea_level_pressure, frame.soil_temperature_10,
            frame.soil_temperature_30, frame.soil_temperature_00)

        query = data.query_database(config.main_db_path, QUERY, values)
        
        if query == True:
            if config.report_uploading == True:
                query = data.query_database(config.upload_db_path, QUERY, values)

                if query == False:
                    helpers.data_error("operation_log_report() 5")
        else: helpers.data_error("operation_log_report() 4")

        print(frame.air_temperature)
        print(frame.rainfall)


def operation_log_environment(utc):
    """ Reads computer environment sensors and saves the data to the database
    """
    global CPUT_sensor, EncT_sensor
    frame = data.EnvReportFrame(utc)

    # Read enclosure temperature
    if config.EncT == True:
        EncT_sensor.sample()

        if EncT_sensor.error == False:
            EncT_value = EncT_sensor.get_primary()

            if EncT_value != None:
                frame.enclosure_temperature = round(EncT_value, 1)
                EncT_sensor.reset_primary()
        else: helpers.data_error("operation_log_environment() 0")

    # Process CPU temperature
    if config.envReport_logging == True:
        CPUT_value = CPUT_sensor.get_primary()

        if CPUT_value != None:
            frame.cpu_temperature = round(CPUT_value, 1)
            CPUT_sensor.reset_primary()


    # Write data to database
    QUERY = "INSERT INTO envReports VALUES (?, ?, ?)"
    values = (frame.time.strftime("%Y-%m-%d %H:%M:%S"),
        frame.enclosure_temperature, frame.cpu_temperature)

    query = data.query_database(config.main_db_path, QUERY, values)
    
    if query == True:
        if config.envReport_uploading == True:
            query = data.query_database(config.upload_db_path, QUERY, values)

            if query == False:
                helpers.data_error("operation_log_environment() 2")
    else: helpers.data_error("operation_log_environment() 1")

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

def schedule_minute():
    """ Triggered every minute to generate a report and environment report, add
        them to the database, activate the camera and generate statistics
    """
    global CPUT_sensor
    utc = datetime.utcnow().replace(microsecond=0)

    # Reset LEDS and wait to allow schedule_second() to finish
    if config.data_led_pin != None:
        gpio.output(config.data_led_pin, gpio.HIGH)
    if config.error_led_pin != None:
        gpio.output(config.error_led_pin, gpio.LOW)
    time.sleep(0.25)


    # Read CPU temperature before anything else happens. Considered idle temp
    if config.envReport_logging == True:
        try:
            CPUT_sensor.sample()
        except: helpers.data_error("schedule_minute() 0")


    # Run main logging operations
    operation_log_report(utc)
    if config.envReport_logging == True: operation_log_environment(utc)
    if config.camera_logging == True: operation_log_camera(utc)
    if config.dayStat_logging == True: operation_generate_stats(utc)

    if config.data_led_pin != None:
        gpio.output(config.data_led_pin, gpio.LOW)