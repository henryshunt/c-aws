""" CAWS Data Acquisition Program
      Responsible for logging data parameters and generating statistics
"""

import sys
import subprocess
import os
from datetime import datetime, timedelta
import time
from threading import Thread
import math
import sqlite3
from statistics import mean

import daemon
import Adafruit_GPIO
import RPi.GPIO as gpio
import astral
from apscheduler.schedulers.blocking import BlockingScheduler
import sensors.bme280 as bme280
import sensors.sht31d as sht31d
import sensors.mcp3008 as mcp3008
from gpiozero import CPUTemperature
import pytz
import picamera
import spidev

import routines.config as config
import routines.helpers as helpers
from sensors.temperature import Temperature
# from sensors.humidity import Humidity
# from sensors.wind import Wind
# from sensors.direction import Direction
from sensors.sunshine import Sunshine
from sensors.rainfall import Rainfall
# from sensors.pressure import Pressure
import routines.frames as frames
from routines.frames import DbTable
from routines.mutable import MutableValue
from sensors.logtype import LogType
import routines.data as data
import routines.analysis as analysis
import routines.queries as queries

data_start = None
disable_sampling = True

sensor_AirT = Temperature()
sensor_ExpT = Temperature()
# sensor_RelH = Humidity()
# sensor_WSpd = Wind()
# sensor_WDir = Direction()
sensor_SunD = Sunshine()
sensor_Rain = Rainfall()
# sensor_StaP = Pressure()
sensor_ST10 = Temperature()
sensor_ST30 = Temperature()
sensor_ST00 = Temperature()
# sensor_CPUT = CPUTemperature()
sensor_EncT = Temperature()

RelH_samples = []
WSpd_ticks = []
past_WSpd_ticks = []
WDir_samples = []
past_WDir_samples = []
SunD_ticks = 0
Rain_ticks = 0
StaP_samples = []


def do_log_report(utc):
    """ Reads all sensors, calculates derived and averaged parameters, and
        saves the data to the database
    """
    global disable_sampling, data_start, AirT_samples, RelH_samples, WSpd_ticks
    global past_WSpd_ticks, WDir_samples, past_WDir_samples, SunD_ticks
    global Rain_ticks, StaP_samples

    frame = frames.DataUtcReport(utc)
    ten_mins_ago = frame.time - timedelta(minutes = 10)
    two_mins_ago = frame.time - timedelta(minutes = 2)
    
    # -- COPY GLOBALS ----------------------------------------------------------
    disable_sampling = True
    sensor_Rain.set_pause(True)

    sensor_AirT.shift_store()
    sensor_AirT.reset_store()
    new_RelH_samples = RelH_samples[:]
    RelH_samples = []
    new_WSpd_ticks = WSpd_ticks[:]
    WSpd_ticks = []
    new_WDir_samples = WDir_samples[:]
    WDir_samples = []
    sensor_SunD.shift_store()
    sensor_SunD.reset_store()
    sensor_Rain.shift_store()
    sensor_Rain.reset_store()
    new_StaP_samples = StaP_samples[:]
    StaP_samples = []

    disable_sampling = False
    sensor_Rain.set_pause(False)

    # -- INSTANTANEOUS TEMPERATURES --------------------------------------------
    try:
        # Read each sensor in separate thread to reduce wait
        ExpT_value = MutableValue()
        ExpT_thread = None

        if config.log_ExpT == True:
            ExpT_thread = Thread(target = ds18b20.read_temperature, args = (
                config.ExpT_address, ExpT_value))
            ExpT_thread.start()

        ST10_value = MutableValue()
        ST10_thread = None

        if config.log_ST10 == True:
            ST10_thread = Thread(target = ds18b20.read_temperature, args = (
                config.ST10_address, ST10_value))
            ST10_thread.start()

        ST30_value = MutableValue()
        ST30_thread = None
        
        if config.log_ST30 == True:
            ST30_thread = Thread(target = ds18b20.read_temperature, args = (
                config.ST30_address, ST30_value))
            ST30_thread.start()

        ST00_value = MutableValue()
        ST00_thread = None
        
        if config.log_ST00 == True:
            ST00_thread = Thread(target = ds18b20.read_temperature, args = (
                config.ST00_address, ST00_value))
            ST00_thread.start()

        # Wait for all sensors to finish reading
        if config.log_ExpT == True: ExpT_thread.join()
        if config.log_ST10 == True: ST10_thread.join()
        if config.log_ST30 == True: ST30_thread.join()
        if config.log_ST00 == True: ST00_thread.join()

        # Get and check read values from each temperature sensor
        if config.log_ExpT == True:
            if ExpT_value.getValue() == None: helpers.data_error()
            else: frame.exposed_temperature = round(ExpT_value.getValue(), 1)

        if config.log_ST10 == True:
            if ST10_value.getValue() == None: helpers.data_error()
            else: frame.soil_temperature_10 = round(ST10_value.getValue(), 1)

        if config.log_ST30 == True:
            if ST30_value.getValue() == None: helpers.data_error()
            else: frame.soil_temperature_30 = round(ST30_value.getValue(), 1)

        if config.log_ST00 == True:
            if ST00_value.getValue() == None: helpers.data_error()
            else: frame.soil_temperature_00 = round(ST00_value.getValue(), 1)
    except: helpers.data_error()

    # -- AIR TEMPERATURE -------------------------------------------------------
    if config.log_AirT == True:
        try:
            AirT_value = sensor_AirT.get_shifted()
            sensor_AirT.reset_shift()

            if AirT_value != None:
                frame.air_temperature = round(AirT_value, 1)
        except: helpers.data_error()

    # -- RELATIVE HUMIDITY -----------------------------------------------------
    if config.log_RelH == True:
        try:
            if len(new_RelH_samples) > 0:
                frame.relative_humidity = round(mean(new_RelH_samples), 1)
        except: helpers.data_error()
    
    # -- WIND SPEED AND WIND GUST ----------------------------------------------
    if config.log_WSpd == True or config.log_WGst == True:
        data.prepare_wind_ticks(past_WSpd_ticks, new_WSpd_ticks, ten_mins_ago)

    # -- WIND SPEED ------------------------------------------------------------
    if config.log_WSpd == True:
        try:
            if two_mins_ago >= data_start:
                WSpd_value = data.calculate_wind_speed(past_WSpd_ticks,
                    two_mins_ago)
                
                if WSpd_value != None: frame.wind_speed = round(WSpd_value, 1)
        except: helpers.data_error()

    # -- WIND DIRECTION --------------------------------------------------------
    if config.log_WDir == True:
        try:
            if two_mins_ago >= data_start:
                WDir_value = data.calculate_wind_direction(past_WDir_samples,
                    new_WDir_samples, two_mins_ago)

                if WDir_value != None:
                    frame.wind_direction = int(round(WDir_value))
        except: helpers.data_error()

    # -- WIND GUST -------------------------------------------------------------
    if config.log_WGst == True:
        try:
            if ten_mins_ago >= data_start:
                WGst_value = data.calculate_wind_gust(past_WSpd_ticks,
                    ten_mins_ago)

                if WGst_value != None: frame.wind_gust = round(WGst_value, 1)
        except: helpers.data_error()

    # -- SUNSHINE DURATION -----------------------------------------------------
    if config.log_SunD == True:
        try:
            SunD_value = sensor_SunD.get_shifted()
            sensor_SunD.reset_shift()

            if SunD_value != None:
                frame.sunshine_duration = SunD_value
        except: helpers.data_error()

    # -- RAINFALL --------------------------------------------------------------
    if config.log_Rain == True:
        try:
            frame.rainfall = new_Rain_ticks * 0.254
        except: helpers.data_error()

    # -- STATION PRESSURE ------------------------------------------------------
    if config.log_StaP == True:
        try:
            if len(new_StaP_samples) > 0:
                frame.station_pressure = round(mean(new_StaP_samples), 1)
        except: helpers.data_error()

    # -- DEW POINT -------------------------------------------------------------
    if config.log_DewP == True:
        try:
            DewP_value = data.calculate_dew_point(frame.air_temperature,
                frame.relative_humidity)

            if DewP_value != None: frame.dew_point = round(DewP_value, 1)
        except: helpers.data_error()

    # -- MEAN SEA LEVEL PRESSURE -----------------------------------------------
    if config.log_MSLP == True:
        try:
            MSLP_value = data.calculate_mean_sea_level_pressure(
                frame.station_pressure, frame.air_temperature,
                frame.dew_point)

            if MSLP_value != None:
                frame.mean_sea_level_pressure = round(MSLP_value, 1)
        except: helpers.data_error()

    # ADD TO DATABASE ----------------------------------------------------------
    free_space = helpers.remaining_space("/")

    if free_space == None or free_space < 0.1:
        helpers.data_error()
        return
        
    try:
        with sqlite3.connect(config.database_path) as database:
            cursor = database.cursor()
            cursor.execute(queries.INSERT_REPORT,
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
            
            database.commit()
    except: helpers.data_error()

def do_log_environment(utc, CPUT_value):
    """ Reads computer environment sensors and saves the data to the database
    """
    frame = frames.DataUtcEnviron(utc)

    # -- ENCLOSURE TEMPERATURE -------------------------------------------------
    if config.log_EncT == True:
        try:
            EncT_value = ds18b20.read_temperature(config.EncT_address, None)

            if EncT_value == None: helpers.data_error()
            else: frame.enclosure_temperature = round(EncT_value, 1)
        except: helpers.data_error()

    # -- CPU TEMPERATURE -------------------------------------------------------
    if config.log_CPUT == True:
        try:
            if CPUT_value == None: helpers.data_error()
            else: frame.cpu_temperature = round(CPUT_value, 1)
        except: helpers.data_error()

    # -- ADD TO DATABASE -------------------------------------------------------
    free_space = helpers.remaining_space("/")

    if free_space == None or free_space < 0.1:
        helpers.data_error()
        return

    try:
        with sqlite3.connect(config.database_path) as database:
            cursor = database.cursor()
            cursor.execute(queries.INSERT_ENVREPORT,
                               (frame.time.strftime("%Y-%m-%d %H:%M:%S"),
                                frame.enclosure_temperature,
                                frame.cpu_temperature))
            
            database.commit()
    except: helpers.data_error()

def do_log_camera(utc):
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

        # Check free space on camera drive
        free_space = helpers.remaining_space(config.camera_drive)

        if free_space == None or free_space < 0.1:
            helpers.data_error()
            return

        # -- CAMERA -----------------------------------------------------------
        try:
            image_dir = os.path.join(config.camera_drive,
                                     utc.strftime("%Y/%m/%d"))
            if not os.path.exists(image_dir): os.makedirs(image_dir)
            image_name = utc.strftime("%Y-%m-%dT%H-%M-%S")
        
            # Set image resolution, wait for auto settings, and capture
            with picamera.PiCamera() as camera:
                camera.resolution = (1280, 960)
                time.sleep(2.5)
                camera.capture(os.path.join(image_dir, image_name + ".jpg"))
        except: helpers.data_error()

def do_generate_stats(utc):
    """ Generates statistics for the local current day from logged records and
        saves them to the database
    """
    local_time = helpers.utc_to_local(utc)

    # -- GET NEW STATS ---------------------------------------------------------
    new_stats = analysis.stats_for_date(local_time)

    if new_stats == False:
        helpers.data_error()
        return

    # -- GET CURRENT STATS -----------------------------------------------------
    cur_stats = analysis.record_for_time(local_time, DbTable.DAYSTATS)

    if cur_stats == False:
        helpers.data_error()
        return

    # -- ADD TO DATABASE -------------------------------------------------------
    free_space = helpers.remaining_space("/")

    if free_space == None or free_space < 0.1:
        helpers.data_error()
        return

    try:
        with sqlite3.connect(config.database_path) as database:
            cursor = database.cursor()

            # Insert or update depending on status of current statistic
            if cur_stats == None:
                cursor.execute(queries.INSERT_DAYSTAT,
                    (local_time.strftime("%Y-%m-%d"),
                     new_stats["AirT_Avg"], new_stats["AirT_Min"],
                     new_stats["AirT_Max"], new_stats["RelH_Avg"],
                     new_stats["RelH_Min"], new_stats["RelH_Max"],
                     new_stats["DewP_Avg"], new_stats["DewP_Min"],
                     new_stats["DewP_Max"], new_stats["WSpd_Avg"],
                     new_stats["WSpd_Min"], new_stats["WSpd_Max"],
                     new_stats["WDir_Avg"], new_stats["WDir_Min"],
                     new_stats["WDir_Max"], new_stats["WGst_Avg"],
                     new_stats["WGst_Min"], new_stats["WGst_Max"],
                     new_stats["SunD_Ttl"], new_stats["Rain_Ttl"],
                     new_stats["MSLP_Avg"], new_stats["MSLP_Min"],
                     new_stats["MSLP_Max"], new_stats["ST10_Avg"],
                     new_stats["ST10_Min"], new_stats["ST10_Max"],
                     new_stats["ST30_Avg"], new_stats["ST30_Min"],
                     new_stats["ST30_Max"], new_stats["ST00_Avg"],
                     new_stats["ST00_Min"], new_stats["ST00_Max"]))
                
            else:
                cursor.execute(queries.UPDATE_DAYSTAT,
                    (new_stats["AirT_Avg"], new_stats["AirT_Min"],
                     new_stats["AirT_Max"], new_stats["RelH_Avg"],
                     new_stats["RelH_Min"], new_stats["RelH_Max"],
                     new_stats["DewP_Avg"], new_stats["DewP_Min"],
                     new_stats["DewP_Max"], new_stats["WSpd_Avg"],
                     new_stats["WSpd_Min"], new_stats["WSpd_Max"],
                     new_stats["WDir_Avg"], new_stats["WDir_Min"],
                     new_stats["WDir_Max"], new_stats["WGst_Avg"],
                     new_stats["WGst_Min"], new_stats["WGst_Max"],
                     new_stats["SunD_Ttl"], new_stats["Rain_Ttl"],
                     new_stats["MSLP_Avg"], new_stats["MSLP_Min"],
                     new_stats["MSLP_Max"], new_stats["ST10_Avg"],
                     new_stats["ST10_Min"], new_stats["ST10_Max"],
                     new_stats["ST30_Avg"], new_stats["ST30_Min"],
                     new_stats["ST30_Max"], new_stats["ST00_Avg"],
                     new_stats["ST00_Min"], new_stats["ST00_Max"],
                     local_time.strftime("%Y-%m-%d")))
            
            database.commit()
    except: helpers.data_error()


def every_minute():
    """ Triggered every minute to generate a report and environment report, add
        them to the database, activate the camera and generate statistics
    """
    utc = datetime.utcnow().replace(second = 0, microsecond = 0)

    # Reset LEDS and wait to allow every_second() to finish
    gpio.output(helpers.DATALEDPIN, gpio.HIGH)
    gpio.output(helpers.ERRORLEDPIN, gpio.LOW)
    time.sleep(0.25)

    # -- CPU TEMPERATURE -------------------------------------------------------
    CPUT_value = None

    # Read CPU temperature before anything else happens. Considered idle temp
    if config.log_CPUT == True:
        try:
            CPUT_value = CPUTemperature().temperature
        except: helpers.data_error()

    # -- RUN OPERATIONS --------------------------------------------------------
    do_log_report(utc)
    if config.envReport_logging == True: do_log_environment(utc, CPUT_value)
    if config.camera_logging == True: do_log_camera(utc)
    if config.dayStat_generation == True: do_generate_stats(utc)
    gpio.output(23, gpio.LOW)

def every_second():
    """ Triggered every second to read sensor values into a list for averaging
    """
    utc = datetime.utcnow().replace(microsecond = 0)

    global disable_sampling
    if disable_sampling == True: return

    # -- SUNSHINE DURATION -----------------------------------------------------
    if config.log_SunD == True:
        try:
            sensor_SunD.sample()
        except: helpers.data_error()

    if str(utc.second) == "0": return

    # -- AIR TEMPERATURE -------------------------------------------------------
    AirT_thread = None

    if config.log_AirT == True:
        try:
            AirT_thread = Thread(target = sensor_AirT.sample, args = ())
            AirT_thread.start()
        except: helpers.data_error()

    # -- RELATIVE HUMIDITY -----------------------------------------------------
    if config.log_RelH == True:
        try:
            global RelH_samples

            RelH_samples.append(
                round(sht31d.SHT31(address = 0x44).read_humidity(), 1))
        except: helpers.data_error()

    # -- WIND DIRECTION --------------------------------------------------------
    if config.log_WDir == True:
        global WDir_samples
        spi = None

        try:
            spi = Adafruit_GPIO.SPI.SpiDev(0, 0)
            adc = mcp3008.MCP3008(spi = spi)

            # Read sensor value from analog to digital converter
            adc_value = adc.read_adc(1)

            # Convert ADC value to degrees
            if adc_value >= 52 and adc_value <= 976:
                WDir_degrees = (adc_value - 52) / (976 - 52) * (360 - 0)

                # Modify value to account for non-zero-degrees at north
                WDir_degrees -= 148
                if WDir_degrees >= 360: WDir_degrees -= 360
                elif WDir_degrees < 0: WDir_degrees += 360

                # Add to sample list with timestamp
                if WDir_degrees >= 359.5: WDir_degrees = 0
                WDir_samples.append((utc, int(round(WDir_degrees))))
        except: helpers.data_error()

        if spi != None: spi.close()

    # -- STATION PRESSURE ------------------------------------------------------
    if config.log_StaP == True:
        try:
            global StaP_samples
            StaP_sensor = bme280.BME280(p_mode = bme280.BME280_OSAMPLE_8)

            # Temperature must be read first or pressure will not return
            discard_StaP_temp = StaP_sensor.read_temperature()
            StaP_samples.append(round(StaP_sensor.read_pressure() / 100, 1))
        except: helpers.data_error()

    # -- AIR TEMPERATURE -------------------------------------------------------
    if config.log_AirT == True:
        try:
            AirT_thread.join()
            if sensor_AirT.get_error() == True: helpers.data_error()
        except: helpers.data_error()


def do_trigger_wspd(channel):
    global disable_sampling, WSpd_ticks
    if disable_sampling == True: return
    
    WSpd_ticks.append(datetime.utcnow())


# ENTRY POINT ==================================================================
def entry_point():
    global data_start, disable_sampling
    config.load()

    # -- INIT GPIO AND LEDS ----------------------------------------------------
    gpio.setwarnings(False)
    gpio.setmode(gpio.BCM)

    # Setup and reset the data and error LEDs
    gpio.setup(helpers.DATALEDPIN, gpio.OUT)
    gpio.output(helpers.DATALEDPIN, gpio.LOW)
    gpio.setup(helpers.ERRORLEDPIN, gpio.OUT)
    gpio.output(helpers.ERRORLEDPIN, gpio.LOW)

    # -- SET UP SENSORS --------------------------------------------------------
    if config.log_AirT == True:
        sensor_AirT.setup(LogType.ARRAY, config.AirT_address)
    if config.log_ExpT == True:
        sensor_ExpT.setup(LogType.ARRAY, config.ExpT_address)

    if config.log_WSpd == True:
        gpio.setup(27, gpio.IN, pull_up_down = gpio.PUD_DOWN)
        gpio.add_event_detect(27, gpio.FALLING, callback = do_trigger_wspd,
            bouncetime = 1)

    if config.log_SunD == True: sensor_SunD.setup(25)
    if config.log_Rain == True: sensor_Rain.setup(22)

    if config.log_ST10 == True:
        sensor_ST10.setup(LogType.ARRAY, config.ST10_address)
    if config.log_ST30 == True:
        sensor_ST30.setup(LogType.ARRAY, config.ST30_address)
    if config.log_ST00 == True:
        sensor_ST00.setup(LogType.ARRAY, config.ST00_address)

    if config.log_EncT == True:
        sensor_EncT.setup(LogType.ARRAY, config.EncT_address)

    # -- WAIT FOR MINUTE -------------------------------------------------------
    while datetime.utcnow().second != 0:
        gpio.output(helpers.DATALEDPIN, gpio.HIGH)
        time.sleep(0.1)
        gpio.output(helpers.DATALEDPIN, gpio.LOW)
        time.sleep(0.1)

    # -- START DATA LOGGING ----------------------------------------------------
    data_start = datetime.utcnow().replace(second = 0, microsecond = 0)
    disable_sampling = False
    sensor_Rain.set_pause(False)

    event_scheduler = BlockingScheduler()
    event_scheduler.add_job(every_minute, "cron", minute = "0-59")
    event_scheduler.add_job(every_second, "cron", second = "0-59")
    event_scheduler.start()

if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.realpath(__file__))

    with daemon.DaemonContext(working_directory = current_dir):
        entry_point()