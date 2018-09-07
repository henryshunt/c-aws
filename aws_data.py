""" CAWS Data Acquisition Program
      Responsible for logging data parameters and generating statistics
"""

# DEPENDENCIES -----------------------------------------------------------------
import sys
import subprocess
import os
from datetime import datetime, timedelta
import time
from threading import Thread
import math
import sqlite3
import spidev

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

from config import ConfigData
import helpers
import frames
from frames import DbTable
import analysis
import queries

# GLOBAL VARIABLES -------------------------------------------------------------
config = ConfigData()
data_start = None
disable_sampling = True

WSpd_ticks = []
past_WSpd_ticks = []
WDir_samples = []
past_WDir_samples = []
SunD_ticks = 0
Rain_ticks = 0

AirT_value = None
ExpT_value = None
ST10_value = None
ST30_value = None
ST00_value = None
EncT_value = None
CPUT_value = None

# HELPERS ----------------------------------------------------------------------
def read_temperature(address, is_first_read):
    """ Reads the value of a DS18B20 temperature probe via its address, into its
        global variable
    """
    if not os.path.isdir("/sys/bus/w1/devices/" + address):
        gpio.output(24, gpio.HIGH); return

    try:
        # Read the probe and convert its value to a degC float
        with open("/sys/bus/w1/devices/" + address + "/w1_slave", "r") as probe:
            data = probe.readlines()
            temp = int(data[1][data[1].find("t=") + 2:]) / 1000

            # Check for error values
            if temp == -127: gpio.output(24, gpio.HIGH); return
            if temp == 85:
                if is_first_read == True:
                    read_temperature(address, False); return
                else: gpio.output(24, gpio.HIGH); return

            # Store value in respective global variable
            if address == "28-04167053d6ff":
                global AirT_value; AirT_value = round(temp, 1)
            elif address == "28-0416704a38ff":
                global ExpT_value; ExpT_value = round(temp, 1)
            elif address == "28-0416705d66ff":
                global ST10_value; ST10_value = round(temp, 1)
            elif address == "28-04167055d5ff":
                global ST30_value; ST30_value = round(temp, 1)
            elif address == "28-0516704dc0ff":
                global ST00_value; ST00_value = round(temp, 1)
            elif address == "28-8000001f88fa":
                global EncT_value; EncT_value = round(temp, 1)
    except: gpio.output(24, gpio.HIGH)

# OPERATIONS -------------------------------------------------------------------
def do_log_report(utc):
    """ Reads all sensors, calculates derived and averaged parameters, and saves
        the data to the database
    """
    global config, disable_sampling, data_start, WSpd_ticks, past_WSpd_ticks
    global WDir_samples, past_WDir_samples, SunD_ticks, Rain_ticks, AirT_value
    global ExpT_value, ST10_value, ST30_value, ST00_value

    # Create a frame to store the data and set its time
    frame = frames.DataUtcReport()
    frame.time = utc
    
    # -- COPY GLOBALS ----------------------------------------------------------
    disable_sampling = True
    new_WSpd_ticks = WSpd_ticks[:]
    WSpd_ticks = []
    new_WDir_samples = WDir_samples[:]
    WDir_samples = []
    new_SunD_ticks = SunD_ticks
    SunD_ticks = 0
    new_Rain_ticks = Rain_ticks
    Rain_ticks = 0
    disable_sampling = False

    # -- TEMPERATURE -----------------------------------------------------------
    try:
        AirT_thread = Thread(target = read_temperature,
            args = ("28-04167053d6ff", True)); AirT_thread.start()
        ExpT_thread = Thread(target = read_temperature,
            args = ("28-0416704a38ff", True)); ExpT_thread.start()
        ST10_thread = Thread(target = read_temperature,
            args = ("28-0416705d66ff", True)); ST10_thread.start()
        ST30_thread = Thread(target = read_temperature,
            args = ("28-04167055d5ff", True)); ST30_thread.start()
        ST00_thread = Thread(target = read_temperature,
            args = ("28-0516704dc0ff", True)); ST00_thread.start()

        # Read each temp sensor in separate thread to reduce wait time
        AirT_thread.join(); frame.air_temperature = AirT_value
        ExpT_thread.join(); frame.exposed_temperature = ExpT_value
        ST10_thread.join(); frame.soil_temperature_10 = ST10_value
        ST30_thread.join(); frame.soil_temperature_30 = ST30_value
        ST00_thread.join(); frame.soil_temperature_00 = ST00_value
    except: gpio.output(24, gpio.HIGH)

    AirT_value = None; ExpT_value = None; ST10_value = None
    ST30_value = None; ST00_value = None

    # -- RELATIVE HUMIDITY -----------------------------------------------------
    try:
        frame.relative_humidity = round(
            sht31d.SHT31(address = 0x44).read_humidity(), 1)
    except: gpio.output(24, gpio.HIGH)

    # -- STATION PRESSURE ------------------------------------------------------
    try:
        StaP_sensor = bme280.BME280(p_mode = bme280.BME280_OSAMPLE_8)

        # Temperature must be read first or pressure will not return
        discard_StaP_temp = StaP_sensor.read_temperature()
        frame.station_pressure = round(StaP_sensor.read_pressure() / 100, 1)
    except: gpio.output(24, gpio.HIGH)
        
    # -- WIND SPEED ------------------------------------------------------------
    ten_mins_ago = frame.time - timedelta(minutes = 10)
    two_mins_ago = frame.time - timedelta(minutes = 2)
    
    try:
        # Add new minute ticks to end of past ten minute tick list
        past_WSpd_ticks.extend(new_WSpd_ticks)

        # Remove ticks older than 10 minutes
        for tick in list(past_WSpd_ticks):
            if tick < ten_mins_ago: past_WSpd_ticks.remove(tick)

        # Calculate wind speed only if 2 minutes of data is available
        if two_mins_ago >= data_start:
            WSpd_total = 0

            # Iterate over data in three second samples
            for second in range(0, 118, 3):
                WSpd_start = two_mins_ago + timedelta(seconds = second)
                WSpd_end = WSpd_start + timedelta(seconds = 3)
                ticks_in_WSpd_sample = 0

                # Calculate three second average wind speed and check if highest
                for tick in past_WSpd_ticks:
                    if tick >= WSpd_start and tick < WSpd_end:
                        ticks_in_WSpd_sample += 1

                WSpd_sample = (ticks_in_WSpd_sample * 2.5) / 3
                WSpd_total += WSpd_sample
                
            frame.wind_speed = round(WSpd_total / 40, 1)
    except: gpio.output(24, gpio.HIGH)

    # -- WIND DIRECTION --------------------------------------------------------
    try:
        # Add new minute samples to end of past two minute sample list
        past_WDir_samples.extend(new_WDir_samples)

        # Remove samples older than 2 minutes
        for sample in list(past_WDir_samples):
            if sample[0] < two_mins_ago: past_WDir_samples.remove(sample)

        # Calculate wind direction only if there is positive wind speed
        if (frame.wind_speed != None and frame.wind_speed > 0
            and len(past_WDir_samples) > 0):
            
            WDir_total = 0
            for sample in past_WDir_samples: WDir_total += sample[1]

            frame.wind_direction = int(
                round(WDir_total / len(past_WDir_samples)))
    except: gpio.output(24, gpio.HIGH)

    # -- WIND GUST -------------------------------------------------------------
    try:
        # Calculate wind gust only if there is positive wind speed
        if (frame.wind_speed != None and frame.wind_speed > 0
            and ten_mins_ago >= data_start):

            # Iterate over each second in three second samples
            WGst_value = 0

            for second in range(0, 598):
                WGst_start = ten_mins_ago + timedelta(seconds = second)
                WGst_end = WGst_start + timedelta(seconds = 3)
                ticks_in_WGst_sample = 0

                # Calculate three second average wind speed and check if highest
                for tick in past_WSpd_ticks:
                    if tick >= WGst_start and tick < WGst_end:
                        ticks_in_WGst_sample += 1

                WGst_sample = (ticks_in_WGst_sample * 2.5) / 3
                if WGst_sample > WGst_value: WGst_value = WGst_sample
                
            frame.wind_gust = round(WGst_value, 1)
    except: gpio.output(24, gpio.HIGH)

    # -- SUNSHINE DURATION -----------------------------------------------------
    try:
        frame.sunshine_duration = new_SunD_ticks
    except: gpio.output(24, gpio.HIGH)

    # -- RAINFALL --------------------------------------------------------------
    try:
        if frame.air_temperature != None and frame.exposed_temperature != None:
            if frame.exposed_temperature >= frame.air_temperature + 0.5:
                frame.rainfall = 0
            else: frame.rainfall = new_Rain_ticks * 0.254
    except: gpio.output(24, gpio.HIGH)

    # -- DEW POINT -------------------------------------------------------------
    try:
        if frame.air_temperature != None and frame.relative_humidity != None:
            DewP_a = 0.4343 * math.log(frame.relative_humidity / 100)
            DewP_b = ((8.082 - frame.air_temperature / 556.0)
                      * frame.air_temperature)
            DewP_c = DewP_a + (DewP_b) / (256.1 + frame.air_temperature)
            DewP_d = math.sqrt((8.0813 - DewP_c) ** 2 - (1.842 * DewP_c))

            frame.dew_point = round(278.04 * ((8.0813 - DewP_c) - DewP_d), 1)
    except: gpio.output(24, gpio.HIGH)

    # -- MEAN SEA LEVEL PRESSURE -----------------------------------------------
    try:
        if (frame.station_pressure != None and frame.air_temperature != None and
            frame.dew_point != None):

            MSLP_a = 6.11 * 10 ** ((7.5 * frame.dew_point) / (237.3 +
                                                             frame.dew_point))
            MSLP_b = (9.80665 / 287.3) * config.aws_elevation
            MSLP_c = ((0.0065 * config.aws_elevation) / 2) 
            MSLP_d = frame.air_temperature + 273.15 + MSLP_c + MSLP_a * 0.12
            
            frame.mean_sea_level_pressure = round(
                frame.station_pressure * math.exp(MSLP_b / MSLP_d), 1)
    except: gpio.output(24, gpio.HIGH)

    # ADD TO DATABASE ----------------------------------------------------------
    free_space = helpers.remaining_space("/")
    if free_space == None or free_space < 0.1:
        gpio.output(24, gpio.HIGH); return
        
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
    except: gpio.output(24, gpio.HIGH)

def do_log_environment(utc):
    """ Reads computer environment sensors and saves the data to the database
    """
    global config, EncT_value, CPUT_value
    
    # Create a frame to store the data and set its time
    frame = frames.DataUtcEnviron()
    frame.time = utc

    # -- ENCLOSURE TEMPERATURE -------------------------------------------------
    try:
        read_temperature("28-8000001f88fa", True)
        frame.enclosure_temperature = EncT_value
    except: gpio.output(24, gpio.HIGH)

    # -- CPU TEMPERATURE -------------------------------------------------------
    try:
        frame.cpu_temperature = CPUT_value
    except: gpio.output(24, gpio.HIGH)

    EncT_value = None; CPUT_value = None

    # -- SAVE DATA -------------------------------------------------------------
    free_space = helpers.remaining_space("/")
    if free_space == None or free_space < 0.1: return

    try:
        with sqlite3.connect(config.database_path) as database:
            cursor = database.cursor()
            cursor.execute(queries.INSERT_ENVREPORT,
                               (frame.time.strftime("%Y-%m-%d %H:%M:%S"),
                                frame.enclosure_temperature,
                                frame.cpu_temperature))
            
            database.commit()
    except: gpio.output(24, gpio.HIGH)

def do_log_camera(utc):
    """ Takes an image on the camera if it is currently a five minute interval
        of the hour, and saves it to the camera drive
    """
    global config; utc_minute = str(utc.minute)
    if not utc_minute.endswith("0") and not utc_minute.endswith("5"): return

    # Get sunrise and sunset times for current date
    local_time = helpers.utc_to_local(config, utc).replace(hour = 0, minute = 0)
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
            gpio.output(24, gpio.HIGH); return

        try:
            image_dir = os.path.join(config.camera_drive,
                                     utc.strftime("%Y/%m/%d"))
            if not os.path.exists(image_dir): os.makedirs(image_dir)
            image_name = utc.strftime("%Y-%m-%dT%H-%M-%S")
        
            # Set image resolution, wait for auto settings, and capture
            with picamera.PiCamera() as camera:
                camera.resolution = (1280, 960); time.sleep(2.5)
                camera.capture(os.path.join(image_dir, image_name + ".jpg"))
        except: gpio.output(24, gpio.HIGH)

def do_generate_stats(utc):
    """ Generates statistics for the local current day from logged records and
        saves them to the database
    """
    global config
    local_time = helpers.utc_to_local(config, utc)

    # -- GET NEW STATS ---------------------------------------------------------
    bounds = helpers.day_bounds_utc(config, local_time, False)
    new_stats = analysis.stats_for_date(config, bounds)
    
    if new_stats == False: gpio.output(24, gpio.HIGH); return

    # -- GET CURRENT STATS -----------------------------------------------------
    cur_stats = analysis.record_for_time(config, local_time, DbTable.DAYSTATS)
    if cur_stats == False: gpio.output(24, gpio.HIGH); return

    # -- SAVE DATA -------------------------------------------------------------
    free_space = helpers.remaining_space("/")
    if free_space == None or free_space < 0.1: return

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
    except: gpio.output(24, gpio.HIGH)

# SCHEDULERS -------------------------------------------------------------------
def every_minute():
    """ Triggered every minute to generate a report and environment report, add
        them to the database, activate the camera and generate statistics
    """
    global config
    gpio.output(23, gpio.HIGH)
    gpio.output(24, gpio.LOW)
    utc = datetime.utcnow().replace(second = 0, microsecond = 0)
    time.sleep(0.15)

    # Read CPU temperature before anything else happens. Considered idle temp
    if config.envReport_logging == True:
        try:
            global CPUT_value
            CPUT_value = round(CPUTemperature().temperature, 1)
        except: gpio.output(24, gpio.HIGH)

    # Run actions if relevant configuration modifiers are active
    do_log_report(utc)
    if config.envReport_logging == True: do_log_environment(utc)
    if config.camera_logging == True: do_log_camera(utc)
    if config.dayStat_generation == True: do_generate_stats(utc)
    gpio.output(23, gpio.LOW)

def every_second():
    """ Triggered every second to read sensor values into a list for averaging
    """
    global disable_sampling, WDir_samples, SunD_ticks
    if disable_sampling == True: return

    # -- WIND DIRECTION --------------------------------------------------------
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
            WDir_samples.append((datetime.utcnow(), int(round(WDir_degrees))))
    except: gpio.output(24, gpio.HIGH)

    if spi != None: spi.close()

    # -- SUNSHINE DURATION -----------------------------------------------------
    try:
        if gpio.input(25) == True: SunD_ticks += 1
    except: gpio.output(24, gpio.HIGH)

# INTERRUPTS -------------------------------------------------------------------
def do_trigger_wspd(channel):
    global disable_sampling, WSpd_ticks
    if disable_sampling == True: return
    
    WSpd_ticks.append(datetime.utcnow())

def do_trigger_rain(channel):
    global disable_sampling, Rain_ticks
    if disable_sampling == True: return
        
    Rain_ticks += 1


# ENTRY POINT ==================================================================
def entry_point():
    global config, data_start, disable_sampling; config.load()

    # -- INIT GPIO AND LEDS ----------------------------------------------------
    gpio.setwarnings(False); gpio.setmode(gpio.BCM)
    gpio.setup(23, gpio.OUT); gpio.setup(24, gpio.OUT)
    gpio.output(23, gpio.LOW); gpio.output(24, gpio.LOW)

    # -- SET UP SENSORS --------------------------------------------------------
    gpio.setup(27, gpio.IN, pull_up_down = gpio.PUD_DOWN)
    gpio.add_event_detect(27, gpio.FALLING, callback = do_trigger_wspd,
                        bouncetime = 1)
    gpio.setup(22, gpio.IN, pull_up_down = gpio.PUD_DOWN)
    gpio.add_event_detect(22, gpio.FALLING, callback = do_trigger_rain,
                        bouncetime = 150)
    gpio.setup(25, gpio.IN, pull_up_down = gpio.PUD_DOWN)

    # -- WAIT FOR MINUTE -------------------------------------------------------
    while datetime.utcnow().second != 0:
        gpio.output(23, gpio.HIGH); time.sleep(0.1)
        gpio.output(23, gpio.LOW); time.sleep(0.1)

    # -- START DATA LOGGING ----------------------------------------------------
    data_start = datetime.utcnow().replace(second = 0, microsecond = 0)
    disable_sampling = False

    event_scheduler = BlockingScheduler()
    event_scheduler.add_job(every_minute, "cron", minute = "0-59")
    event_scheduler.add_job(every_second, "cron", second = "0-59")
    event_scheduler.start()

if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.realpath(__file__))
    with daemon.DaemonContext(working_directory = current_dir):
        entry_point()