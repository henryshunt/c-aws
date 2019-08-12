import os
from datetime import datetime, timedelta
import time
from threading import Thread
import sys

import daemon
import RPi.GPIO as gpio
import astral
from apscheduler.schedulers.blocking import BlockingScheduler
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
from sensors.bme280 import BME280
from sensors.cpu import CPU
import routines.data as data
from routines.data import DbTable


AirT_sensor = MCP9808()
ExpT_sensor = DS18B20()
RelH_sensor = HTU21D()
WSpd_sensor = ICA()
WDir_sensor = IEV2()
SunD_sensor = IMSBB()
Rain_sensor = RR111()
StaP_sensor = BME280()
ST10_sensor = DS18B20()
ST30_sensor = DS18B20()
ST00_sensor = DS18B20()
EncT_sensor = DS18B20()
CPUT_sensor = CPU()

disable_sampling = True


def operation_log_report(utc):
    """ Reads all sensors, calculates derived and averaged parameters, and
        saves the data to the database
    """
    global disable_sampling, AirT_sensor, ExpT_sensor, RelH_sensor, WSpd_sensor
    global WDir_sensor, SunD_sensor, Rain_sensor, StaP_sensor, ST10_sensor
    global ST30_sensor, ST00_sensor
    
    frame = data.ReportFrame(utc)
    
    disable_sampling = True
    if config.WSpd == True: WSpd_sensor.pause = True
    if config.Rain == True: Rain_sensor.pause = True

    # Shift and reset sensor stores to allow data collection to continue
    if config.AirT == True:
        AirT_sensor.shift()
        AirT_sensor.reset_primary()
    if config.RelH == True:
        RelH_sensor.shift()
        RelH_sensor.reset_primary()
    if config.WSpd == True:
        WSpd_sensor.shift()
        WSpd_sensor.reset_primary()
    if config.WDir == True:
        WDir_sensor.shift()
        WDir_sensor.reset_primary()
    if config.SunD == True:
        SunD_sensor.shift()
        SunD_sensor.reset_primary()
    if config.Rain == True:
        Rain_sensor.shift()
        Rain_sensor.reset_primary()
    if config.StaP == True:
        StaP_sensor.shift()
        StaP_sensor.reset_primary()

    disable_sampling = False
    if config.WSpd == True: WSpd_sensor.pause = False
    if config.Rain == True: Rain_sensor.pause = False


    # Read exposed air temperature, soil temperature at 10, 30, 100cm in
    # separate threads since DS18B20 sensors each take 0.75s to read
    if config.ExpT == True:
        ExpT_thread = Thread(target=ExpT_sensor.sample, args=())
        ExpT_thread.start()
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
    if config.ExpT == True: ExpT_thread.join()
    if config.ST10 == True: ST10_thread.join()
    if config.ST30 == True: ST30_thread.join()
    if config.ST00 == True: ST00_thread.join()


    # Process air temperature
    if config.AirT == True:
        AirT_value = AirT_sensor.get_secondary()

        if AirT_value != None:
            frame.air_temperature = round(AirT_value, 2)
            AirT_sensor.reset_secondary()

    # Process exposed air temperature
    if config.ExpT == True:
        if ExpT_sensor.get_error() == False: 
            ExpT_value = ExpT_sensor.get_primary()

            if ExpT_value != None:
                frame.exposed_temperature = round(ExpT_value, 1)
                ExpT_sensor.reset_primary()
        else: helpers.data_error(4)

    # Process relative humidity
    if config.RelH == True:
        RelH_value = RelH_sensor.get_secondary()

        if RelH_value != None:
            frame.relative_humidity = round(RelH_value, 1)
            RelH_sensor.reset_secondary()
    
    # Process wind speed
    if config.WSpd == True:
        WSpd_sensor.prepare_secondary(utc)

        WSpd_value = WSpd_sensor.get_secondary()
        if WSpd_value != None:
            frame.wind_speed = round(WSpd_value, 1)

    # Process wind direction
    if config.WDir == True:
        WDir_sensor.prepare_secondary(utc)

        WDir_value = WDir_sensor.get_secondary()
        if WDir_value != None:
            frame.wind_direction = int(round(WDir_value, 0))

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
            frame.station_pressure = round(StaP_value, 1)
            StaP_sensor.reset_secondary()
    
    # Process soil temperature at 10cm
    if config.ST10 == True:
        if ST10_sensor.get_error() == False:
            ST10_value = ST10_sensor.get_primary()

            if ST10_value != None:
                frame.soil_temperature_10 = round(ST10_value, 1)
                ST10_sensor.reset_primary()
        else: helpers.data_error(6)

    # Process soil temperature at 30cm
    if config.ST30 == True:
        if ST30_sensor.get_error() == True:
            ST30_value = ST30_sensor.get_primary()

            if ST30_value != None:
                frame.soil_temperature_30 = round(ST30_value, 1)
                ST30_sensor.reset_primary()
        else: helpers.data_error(8)

    # Process soil temperature at 1m
    if config.ST00 == True:
        if ST00_sensor.get_error() == True:
            ST00_value = ST00_sensor.get_primary()

            if ST00_value != None:
                frame.soil_temperature_00 = round(ST00_value, 1)
                ST00_sensor.reset_primary()
        else: helpers.data_error(10)


    # Derive dew point
    if config.log_DewP == True:
        DewP_value = data.calculate_dew_point(frame.air_temperature,
            frame.relative_humidity)

        if DewP_value != None:
            frame.dew_point = round(DewP_value, 1)

    # Derive wind gust
    if config.log_WGst == True:
        WGst_value = WSpd_sensor.get_wind_gust()
        if WGst_value != None:
            frame.wind_gust = round(WGst_value, 1)

    # Derive mean sea level pressure
    if config.log_MSLP == True:
        MSLP_value = data.calculate_mslp(frame.station_pressure,
            frame.air_temperature, frame.dew_point)

        if MSLP_value != None:
            frame.mean_sea_level_pressure = round(MSLP_value, 1)


    # Write data to database
    write = data.write_record(DbTable.REPORTS,
        (frame.time.strftime("%Y-%m-%d %H:%M:%S"),
         frame.air_temperature,
         frame.exposed_temperature,
         frame.relative_humidity,
         frame.dew_point,
         frame.wind_speed,
         frame.wind_direction,
         frame.wind_gust, 
         frame.sunshine_duration,
         frame.rainfall,
         frame.station_pressure,
         frame.mean_sea_level_pressure,
         frame.soil_temperature_10,
         frame.soil_temperature_30,
         frame.soil_temperature_00))
    if write == False: helpers.data_error(23)

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
        else: helpers.data_error(26)

    # Process CPU temperature
    if config.envReport_logging == True:
        CPUT_value = CPUT_sensor.get_primary()

        if CPUT_value != None:
            frame.cpu_temperature = round(CPUT_value, 1)
            CPUT_sensor.reset_primary()


    # Write data to database
    write = data.write_record(DbTable.ENVREPORTS,
        (frame.time.strftime("%Y-%m-%d %H:%M:%S"),
         frame.enclosure_temperature,
         frame.cpu_temperature))
    if write == False: helpers.data_error(28)

def operation_log_camera(utc):
    """ Takes an image on the camera if it is currently a five minute interval
        of the hour, and saves it to the camera drive
    """    
    utc_minute = str(utc.minute)
    if not utc_minute.endswith("0") and not utc_minute.endswith("5"):
        return

    # Get sunrise and sunset times for current date
    local_time = helpers.utc_to_local(utc).replace(hour = 0, minute = 0)
    location = astral.Location(("", "", config.aws_latitude,
        config.aws_longitude, str(config.aws_time_zone), config.aws_elevation))
    solar = location.sun(date = local_time, local = False)
    
    sunset_threshold = solar["sunset"] + timedelta(minutes = 60)
    sunrise_threshold = solar["sunrise"] - timedelta(minutes = 60)

    # Only take images between sunrise and sunset
    if (utc >= sunrise_threshold.replace(tzinfo = None) and
        utc <= sunset_threshold.replace(tzinfo = None)):

        if (not os.path.isdir(config.camera_directory) or 
            not os.path.ismount(config.camera_directory)):
            helpers.data_error(50)
            return

        free_space = helpers.remaining_space(config.camera_directory)
        if free_space == None or free_space < 0.1:
            helpers.data_error(30)
            return

        # -- CAMERA -----------------------------------------------------------
        try:
            image_dir = os.path.join(config.camera_directory,
                                     utc.strftime("%Y/%m/%d"))
            if not os.path.isdir(image_dir): os.makedirs(image_dir)
            image_name = utc.strftime("%Y-%m-%dT%H-%M-%S")
        
            # Set image resolution, wait for auto settings, and capture
            with picamera.PiCamera() as camera:
                camera.resolution = (1280, 960)
                time.sleep(2.5)
                camera.capture(os.path.join(image_dir, image_name + ".jpg"))
        except: helpers.data_error(31)

def operation_generate_stats(utc):
    """ Generates statistics for the local current day from logged records and
        saves them to the database
    """
    local_time = helpers.utc_to_local(utc)

    # Need to recalculate previous day stats once more as averaged and totalled
    # parameters include the first minute of the next day
    if local_time.hour == 0 and local_time.minute == 0:
        data.generate_write_stats(utc - timedelta(minutes=1))
        
    data.generate_write_stats(utc)


def schedule_minute():
    """ Triggered every minute to generate a report and environment report, add
        them to the database, activate the camera and generate statistics
    """
    global CPUT_sensor
    utc = datetime.utcnow().replace(microsecond=0)

    # Reset LEDS and wait to allow schedule_second() to finish
    gpio.output(helpers.DATALEDPIN, gpio.HIGH)
    gpio.output(helpers.ERRORLEDPIN, gpio.LOW)
    time.sleep(0.25)


    # Read CPU temperature before anything else happens. Considered idle temp
    if config.envReport_logging == True:
        try:
            CPUT_sensor.sample()
        except: helpers.data_error(19)


    # Run main logging operations
    operation_log_report(utc)
    if config.envReport_logging == True: operation_log_environment(utc)
    if config.camera_logging == True: operation_log_camera(utc)
    if config.dayStat_generation == True: operation_generate_stats(utc)

    gpio.output(helpers.DATALEDPIN, gpio.LOW)

def schedule_second():
    """ Triggered every second to read sensor values into a list for averaging
    """
    global disable_sampling, SunD_sensor, AirT_sensor, RelH_sensor, WDir_sensor
    global StaP_sensor
    utc = datetime.utcnow().replace(microsecond=0)

    # No sensor reads if sampling is disabled
    if disable_sampling == True: return

    # Read sunshine duration
    if config.SunD == True:
        try:
            SunD_sensor.sample()
        except: helpers.data_error(14)


    # Prevent reading on 0 second. Previous sensors are totalled, so require the
    # 0 second for the final value. Following sensors are averaged, so the 0 
    # second is part of the next minute and must be not be read since the
    # logging routine runs after the 0 second has passed.
    if str(utc.second) == "0": return


    # Read air temperature
    if config.AirT == True:
        try:
            AirT_sensor.sample()
        except: helpers.data_error(15)

    # Read relative humidity
    if config.RelH == True:
        try:
            RelH_sensor.sample()
        except: helpers.data_error(16)

    # Read wind direction
    if config.WDir == True:
        try:
            WDir_sensor.sample(utc)
        except: helpers.data_error(17)

    # Read station pressure
    if config.StaP == True:
        try:
            StaP_sensor.sample()
        except: helpers.data_error(18)


if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.realpath(__file__))

    with daemon.DaemonContext(working_directory=current_dir):
        if config.load() == False: sys.exit()

        # Set up and reset data and error indicator LEDs
        gpio.setmode(gpio.BCM)

        gpio.setup(helpers.DATALEDPIN, gpio.OUT)
        gpio.output(helpers.DATALEDPIN, gpio.LOW)
        gpio.setup(helpers.ERRORLEDPIN, gpio.OUT)
        gpio.output(helpers.ERRORLEDPIN, gpio.LOW)


        # Set up sensor interfaces
        if config.AirT == True:
            try:
                AirT_sensor.setup(LogType.ARRAY)
            except: helpers.data_error(0)

        if config.ExpT == True:
            try:
                ExpT_sensor.setup(LogType.VALUE, config.ExpT_address)
            except: helpers.data_error(1)

        if config.RelH == True:
            try:
                RelH_sensor.setup(LogType.ARRAY)
            except: helpers.data_error(2)

        if config.WSpd == True:
            try:
                WSpd_sensor.setup(config.WSpd_pin)
            except: helpers.data_error(3)

        if config.WDir == True:
            try:
                WDir_sensor.setup(config.WDir_channel)
            except: helpers.data_error(4)

        if config.SunD == True:
            try:
                SunD_sensor.setup(config.SunD_pin)
            except: helpers.data_error(5)

        if config.Rain == True:
            try:
                Rain_sensor.setup(config.Rain_pin)
            except: helpers.data_error(6)

        if config.StaP == True:
            try:
                StaP_sensor.setup(LogType.ARRAY)
            except: helpers.data_error(7)

        if config.ST10 == True:
            try:
                ST10_sensor.setup(LogType.VALUE, config.ST10_address)
            except: helpers.data_error(8)

        if config.ST30 == True:
            try:
                ST30_sensor.setup(LogType.VALUE, config.ST30_address)
            except: helpers.data_error(9)

        if config.ST00 == True:
            try:
                ST00_sensor.setup(LogType.VALUE, config.ST00_address)
            except: helpers.data_error(10)

        if config.envReport_logging == True:
            try:
                CPUT_sensor.setup(LogType.ARRAY)
            except: helpers.data_error(11)

            if config.EncT == True:
                try:
                    EncT_sensor.setup(LogType.VALUE, config.EncT_address)
                except: helpers.data_error(12)

        if config.camera_logging == True:
            try:
                with picamera.PiCamera() as camera: pass
            except: helpers.data_error(13)


        # Wait for the next minute to start before starting logging
        while datetime.utcnow().second != 0:
            gpio.output(helpers.DATALEDPIN, gpio.HIGH)
            time.sleep(0.1)
            gpio.output(helpers.DATALEDPIN, gpio.LOW)
            time.sleep(0.1)

        # Start data logging
        start_time = datetime.utcnow().replace(microsecond=0)
        WSpd_sensor.start_time = start_time
        Rain_sensor.start_time = start_time

        event_scheduler = BlockingScheduler()
        event_scheduler.add_job(schedule_minute, "cron", minute="0-59")
        event_scheduler.add_job(schedule_second, "cron", second="0-59")

        disable_sampling = False
        WSpd_sensor.pause = False
        Rain_sensor.pause = False
        event_scheduler.start()