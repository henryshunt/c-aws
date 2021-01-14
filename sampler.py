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
        self.AirT_sensor = MCP9808()
        self.RelH_sensor = HTU21D()
        self.WSpd_sensor = ICA()
        self.WDir_sensor = IEV2()
        self.SunD_sensor = IMSBB()
        self.Rain_sensor = RR111()
        self.StaP_sensor = BMP280()
        self.ST10_sensor = DS18B20()
        self.ST30_sensor = DS18B20()
        self.ST00_sensor = DS18B20()
        self.EncT_sensor = DS18B20()
        self.CPUT_sensor = CPU()
        self.start_time = None

    def open(self):
        if config.AirT == True:
            try:
                self.AirT_sensor.open()
            except: helpers.data_error("__main__() 0")

        if config.RelH == True:
            try:
                self.RelH_sensor.setup(LogType.ARRAY)
            except: helpers.data_error("__main__() 2")

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
                self.SunD_sensor.setup(LogType.ARRAY, config.SunD_pin)
            except: helpers.data_error("__main__() 5")

        if config.Rain == True:
            try:
                self.Rain_sensor.setup(config.Rain_pin)
            except: helpers.data_error("__main__() 6")

        if config.StaP == True:
            try:
                self.StaP_sensor.setup(LogType.ARRAY)
            except: helpers.data_error("__main__() 7")

        if config.ST10 == True:
            try:
                self.ST10_sensor.setup(LogType.VALUE, config.ST10_address)
            except: helpers.data_error("__main__() 8")

        if config.ST30 == True:
            try:
                self.ST30_sensor.setup(LogType.VALUE, config.ST30_address)
            except: helpers.data_error("__main__() 9")

        if config.ST00 == True:
            try:
                self.ST00_sensor.setup(LogType.VALUE, config.ST00_address)
            except: helpers.data_error("__main__() 10")

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

    def start(self, time):
        self.start_time = time
        self.WSpd_sensor.pause = False
        self.Rain_sensor.pause = False
        return True

    def sample(self, time):
        """ Triggered every second to read sensor values into a list for averaging
        """
        # print(time)

        # No sensor reads if sampling is disabled
        #if self.disable_sampling == True: return

        # Read sunshine duration
        if config.SunD == True:
            try:
                self.SunD_sensor.sample()
            except: helpers.data_error("schedule_second() 0")


        # Prevent reading on 0 second. Previous sensors are totalled, so require the
        # 0 second for the final value. Following sensors are averaged, so the 0 
        # second is part of the next minute and must be not be read since the
        # logging routine runs after the 0 second has passed.
        if str(time.second) == 0: return


        # Read air temperature
        if config.AirT == True:
            try:
                self.AirT_sensor.sample()
            except: helpers.data_error("schedule_second() 1")

        # Read relative humidity
        if config.RelH == True:
            try:
                self.RelH_sensor.sample()
            except: helpers.data_error("schedule_second() 2")

        # Read wind direction
        if config.WDir == True:
            try:
                self.WDir_sensor.sample(time)
            except: helpers.data_error("schedule_second() 3")

        # Read station pressure
        if config.StaP == True:
            try:
                self.StaP_sensor.sample()
            except: helpers.data_error("schedule_second() 4")

        return True

    def report(self, time):
        """ Reads all sensors, calculates derived and averaged parameters, and
            saves the data to the database
        """
        frame = data.ReportFrame(time)

        # Shift and reset sensor stores to allow data collection to continue
        if config.AirT == True:
            self.AirT_sensor.store.switch_store()
        if config.RelH == True:
            self.RelH_sensor.shift()
            self.RelH_sensor.reset_primary()
        if config.WSpd == True:
            self.WSpd_sensor.shift()
            self.WSpd_sensor.reset_primary()
        if config.WDir == True:
            self.WDir_sensor.shift()
            self.WDir_sensor.reset_primary()
        if config.SunD == True:
            self.SunD_sensor.shift()
            self.SunD_sensor.reset_primary()
        if config.Rain == True:
            self.Rain_sensor.shift()
            self.Rain_sensor.reset_primary()
        if config.StaP == True:
            self.StaP_sensor.shift()
            self.StaP_sensor.reset_primary()

        if config.WSpd == True: self.WSpd_sensor.pause = False
        if config.Rain == True: self.Rain_sensor.pause = False


        # Read exposed air temperature, soil temperature at 10, 30, 100cm in
        # separate threads since DS18B20 sensors each take 0.75s to read
        if config.ST10 == True:
            ST10_thread = Thread(target=ST10_sensor.sample, args=())
            ST10_thread.start()
        if config.ST30 == True:
            ST30_thread = Thread(target=ST30_sensor.sample, args=())
            ST30_thread.start()
        if config.ST00 == True:
            ST00_thread = Thread(target=ST00_sensor.sample, args=())
            ST00_thread.start()

        # Wait for all sensors to finish reading
        if config.ST10 == True: ST10_thread.join()
        if config.ST30 == True: ST30_thread.join()
        if config.ST00 == True: ST00_thread.join()


        # Process air temperature
        if config.AirT == True:
            AirT_value = self.AirT_sensor.get_average()

            if AirT_value != None:
                frame.air_temperature = round(AirT_value, 2)

        # Process relative humidity
        if config.RelH == True:
            RelH_value = RelH_sensor.get_secondary()

            if RelH_value != None:
                frame.relative_humidity = round(RelH_value, 2)
                RelH_sensor.reset_secondary()
        
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
            SunD_value = SunD_sensor.get_secondary()

            if SunD_value != None:
                frame.sunshine_duration = SunD_value
                SunD_sensor.reset_secondary()

        # Process rainfall
        if config.Rain == True:
            Rain_value = Rain_sensor.get_secondary()

            if Rain_value != None:
                frame.rainfall = round(Rain_value, 3)
                Rain_sensor.reset_secondary()

        # Process station pressure
        if config.StaP == True:
            StaP_value = StaP_sensor.get_secondary()

            if StaP_value != None:
                frame.station_pressure = round(StaP_value, 2)
                StaP_sensor.reset_secondary()
        
        # Process soil temperature at 10cm
        if config.ST10 == True:
            if ST10_sensor.error == False:
                ST10_value = ST10_sensor.get_primary()

                if ST10_value != None:
                    frame.soil_temperature_10 = round(ST10_value, 1)
                    ST10_sensor.reset_primary()
            else: helpers.data_error("operation_log_report() 1")

        # Process soil temperature at 30cm
        if config.ST30 == True:
            if ST30_sensor.error == False:
                ST30_value = ST30_sensor.get_primary()

                if ST30_value != None:
                    frame.soil_temperature_30 = round(ST30_value, 1)
                    ST30_sensor.reset_primary()
            else: helpers.data_error("operation_log_report() 2")

        # Process soil temperature at 1m
        if config.ST00 == True:
            if ST00_sensor.error == False:
                ST00_value = ST00_sensor.get_primary()

                if ST00_value != None:
                    frame.soil_temperature_00 = round(ST00_value, 1)
                    ST00_sensor.reset_primary()
            else: helpers.data_error("operation_log_report() 3")

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