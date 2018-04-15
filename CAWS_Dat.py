""" CAWS Data Acquisition Program
      Responsible for measuring and logging data parameters, and for generating
      statistics. This is the entry point for the CAWS software
"""

# DEPENDENCIES -----------------------------------------------------------------
import sys
import subprocess
import os
import picamera
from datetime import datetime, timedelta
import time
import pytz
from threading import Thread
from gpiozero import CPUTemperature
import math
import sqlite3
import RPi.GPIO as gpio
import spidev
import Adafruit_GPIO

import astral
from apscheduler.schedulers.blocking import BlockingScheduler
import bme280
import sht31d
import Adafruit_MCP3008

from config import ConfigData
import helpers
import frames
from frames import DbTable
import analysis
import queries

# MESSAGE ----------------------------------------------------------------------
print("--- Custom Automatic Weather Station ---")
print("Program: Data Acquisition Software")
print("Author:  Henry Hunt")
print("Version: V4.0 (April 2018)")
print("")
print("----------- DO NOT TERMINATE -----------")

# GLOBAL VARIABLES -------------------------------------------------------------
config = ConfigData()
program_start = None
data_start = None
disable_sampling = False

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
def do_read_temp(address):
    """ Reads value of specific temperature probe into its global variable
    """
    if not os.path.isdir("/sys/bus/w1/devices/" + address):
        return #gpio.output(23, gpio.HIGH); return

    try:
        with open("/sys/bus/w1/devices/" + address + "/w1_slave", "r") as probe:
            data = probe.readlines()
            temp = int(data[1][data[1].find("t=") + 2:]) / 1000

            # Check for error value
            if temp == -127 or temp == 85: gpio.output(23, gpio.HIGH); return

            # Store value in respective global variable
            if os.path.basename(address) == "28-04167053d6ff":
                global AirT_value; AirT_value = round(temp, 1)
            elif os.path.basename(address) == "28-0416704a38ff":
                global ExpT_value; ExpT_value = round(temp, 1)
            elif os.path.basename(address) == "28-0416705d66ff":
                global ST10_value; ST10_value = round(temp, 1)
            elif os.path.basename(address) == "28-04167055d5ff":
                global ST30_value; ST30_value = round(temp, 1)
            elif os.path.basename(address) == "28-0516704dc0ff":
                global ST00_value; ST00_value = round(temp, 1)
            elif os.path.basename(address) == "28-8000001f88fa":
                global EncT_value; EncT_value = round(temp, 1)
    except: gpio.output(23, gpio.HIGH)

# OPERATIONS -------------------------------------------------------------------
def do_log_report(utc):
    """ Reads all sensors, calculates derived parameters and saves the data to
        the database
    """
    global WSpd_ticks, past_WSpd_ticks, WDir_samples, past_WDir_samples
    global SunD_ticks, Rain_ticks, AirT_value, ExpT_value, ST10_value
    global ST30_value, ST00_value, disable_sampling

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
        AirT_thread = Thread(target =
            do_read_temp, args = ("28-04167053d6ff",)); AirT_thread.start()
        ExpT_thread = Thread(target =
            do_read_temp, args = ("28-0416704a38ff",)); ExpT_thread.start()
        ST10_thread = Thread(target =
            do_read_temp, args = ("28-0416705d66ff",)); ST10_thread.start()
        ST30_thread = Thread(target =
            do_read_temp, args = ("28-04167055d5ff",)); ST30_thread.start()
        ST00_thread = Thread(target =
            do_read_temp, args = ("28-0516704dc0ff",)); ST00_thread.start()

        # Read all sensors in separate threads to reduce wait time
        AirT_thread.join(); frame.air_temperature = AirT_value
        ExpT_thread.join(); frame.exposed_temperature = ExpT_value
        ST10_thread.join(); frame.soil_temperature_10 = ST10_value
        ST30_thread.join(); frame.soil_temperature_30 = ST30_value
        ST00_thread.join(); frame.soil_temperature_00 = ST00_value
    except: gpio.output(23, gpio.HIGH)

    AirT_value = None; ExpT_value = None; ST10_value = None
    ST30_value = None; ST00_value = None

    # -- RELATIVE HUMIDITY -----------------------------------------------------
    try:
        frame.relative_humidity = round(
            sht31d.SHT31(address = 0x44).read_humidity(), 1)
    except: gpio.output(23, gpio.HIGH)

    # -- STATION PRESSURE ------------------------------------------------------
    try:
        StaP_sensor = bme280.BME280(p_mode = bme280.BME280_OSAMPLE_8)

        # Temperature must be read first or pressure will not return
        discard_StaP_temp = StaP_sensor.read_temperature()
        frame.station_pressure = round(StaP_sensor.read_pressure() / 100, 1)
    except: gpio.output(23, gpio.HIGH)
        
    # -- WIND SPEED ------------------------------------------------------------
    ten_mins_ago = frame.time - timedelta(minutes = 10)
    
    try:
        past_WSpd_ticks.extend(new_WSpd_ticks)

        # Remove ticks older than 10 minutes
        for tick in list(past_WSpd_ticks):
            if tick < ten_mins_ago: past_WSpd_ticks.remove(tick)

        # Calculate wind speed only if 10 minutes of data is available
        if ten_mins_ago >= data_start:
            frame.wind_speed = round((len(past_WSpd_ticks) * 2.5) / 600, 1)
    except: gpio.output(23, gpio.HIGH)

    # -- WIND DIRECTION --------------------------------------------------------
    try:
        past_WDir_samples.extend(new_WDir_samples)

        # Remove samples older than 10 minutes
        for sample in list(past_WDir_samples):
            if sample[0] < ten_mins_ago: past_WDir_samples.remove(sample)

        # Calculate wind direction only if there is positive wind speed
        if frame.wind_speed != None:
            if frame.wind_speed > 0 and len(past_WDir_samples) > 0:
                WDir_total = 0
                for sample in past_WDir_samples: WDir_total += sample[1]

                frame.wind_direction = int(round(WDir_total
                                                 / len(past_WDir_samples)))
    except: gpio.output(23, gpio.HIGH)

    # -- WIND GUST -------------------------------------------------------------
    try:
        # Calculate wind gust only if there is positive wind speed
        if frame.wind_speed != None:
            if frame.wind_speed > 0:
                WGst_value = 0

                # Iterate over each second in three second samples
                for second in range(0, 598):
                    WGst_start = ten_mins_ago + timedelta(seconds = second)
                    WGst_end = WGst_start + timedelta(seconds = 3)
                    ticks_in_WGst_sample = 0

                    # Calculate three second average wind speed
                    for tick in past_WSpd_ticks:
                        if tick >= WGst_start and tick < WGst_end:
                            ticks_in_WGst_sample += 1

                    WGst_sample = (ticks_in_WGst_sample * 2.5) / 3
                    if WGst_sample > WGst_value: WGst_value = WGst_sample
                    
                frame.wind_gust = round(WGst_value, 1)
    except: gpio.output(23, gpio.HIGH)

    # -- SUNSHINE DURATION -----------------------------------------------------
    try:
        frame.sunshine_duration = new_SunD_ticks
    except: gpio.output(23, gpio.HIGH)

    # -- RAINFALL --------------------------------------------------------------
    try:
        frame.rainfall = new_Rain_ticks * 0.254
    except: gpio.output(23, gpio.HIGH)

    # -- DEW POINT -------------------------------------------------------------
    try:
        if (frame.air_temperature != None and
            frame.relative_humidity != None):

            DewP_a = 0.4343 * math.log(frame.relative_humidity / 100)
            DewP_b = ((8.082 - frame.air_temperature / 556.0)
                      * frame.air_temperature)
            DewP_c = DewP_a + (DewP_b) / (256.1 + frame.air_temperature)
            DewP_d = math.sqrt((8.0813 - DewP_c) ** 2 - (1.842 * DewP_c))
            
            frame.dew_point = round(278.04 * ((8.0813 - DewP_c) - DewP_d), 1)
    except: gpio.output(23, gpio.HIGH)

    # -- MEAN SEA LEVEL PRESSURE -----------------------------------------------
    try:
        if (frame.station_pressure != None and
            frame.air_temperature != None and
            frame.dew_point != None):

            MSLP_a = 6.11 * 10 ** ((7.5 * frame.dew_point) / (237.3 +
                                                             frame.dew_point))
            MSLP_b = (9.80665 / 287.3) * config.caws_elevation
            MSLP_c = ((0.0065 * config.caws_elevation) / 2) 
            MSLP_d = frame.air_temperature + 273.15 + MSLP_c + MSLP_a * 0.12
            
            frame.mean_sea_level_pressure = round(
                frame.station_pressure * math.exp(MSLP_b / MSLP_d), 1)
    except: gpio.output(23, gpio.HIGH)

    # -- PRESSURE TENDENCY -----------------------------------------------------
    try:
        if frame.station_pressure != None:
            three_hours_ago = frame.time - timedelta(hours = 3)
            record_then = analysis.record_for_time(config, three_hours_ago,
                                                   DbTable.UTCREPORTS)

            # Calculate difference between pressure 3 hours ago
            if record_then != False and record_then != None:
                if record_then["StaP"] != None:
                    frame.pressure_tendency = round(
                        frame.station_pressure - record_then["StaP"], 1)
    except: gpio.output(23, gpio.HIGH)

    # ADD TO DATABASE ----------------------------------------------------------
    free_space = helpers.remaining_space("/")
    if free_space == None or free_space < 0.1:
        gpio.output(23, gpio.HIGH); return
        
    try:
        with sqlite3.connect(config.database_path) as database:
            cursor = database.cursor()
            cursor.execute(queries.INSERT_SINGLE_UTCREPORTS,
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
                                frame.pressure_tendency,
                                frame.mean_sea_level_pressure,
                                frame.soil_temperature_10,
                                frame.soil_temperature_30,
                                frame.soil_temperature_00))
            
            database.commit()
    except: gpio.output(23, gpio.HIGH)

def do_log_environment(utc):
    """ Reads CAWS environment sensors and saves the data to the database
    """
    global EncT_value, CPUT_value
    frame = frames.DataUtcEnviron()
    frame.time = utc

    # -- ENCLOSURE TEMPERATURE -------------------------------------------------
    try:
        do_read_temp("28-8000001f88fa")
        frame.enclosure_temperature = EncT_value
    except: gpio.output(23, gpio.HIGH)

    # -- CPU TEMPERATURE -------------------------------------------------------
    try:
        frame.cpu_temperature = CPUT_value
    except: gpio.output(23, gpio.HIGH)

    EncT_value = None; CPUT_value = None

    # -- SAVE DATA -------------------------------------------------------------
    free_space = helpers.remaining_space("/")
    if free_space == None or free_space < 0.1:
        gpio.output(23, gpio.HIGH); return

    try:
        with sqlite3.connect(config.database_path) as database:
            cursor = database.cursor()
            cursor.execute(queries.INSERT_SINGLE_UTCENVIRON,
                               (frame.time.strftime("%Y-%m-%d %H:%M:%S"),
                                frame.enclosure_temperature,
                                frame.cpu_temperature))
            
            database.commit()
    except: gpio.output(23, gpio.HIGH)

def do_log_camera(utc):
    """ Takes an image every if it is currently a five minute interval, on the
        connected camera, and saves it to the camera drive
    """
    if not str(utc.minute).endswith("0") and not str(utc.minute).endswith("5"):
        return

    # Get sunrise and sunset times for current date
    location = astral.Location(
        ("", "", config.caws_latitude, config.caws_longitude, "UTC",
         config.caws_elevation))
    solar = location.sun(date = utc, local = False)
    
    sunset_threshold = solar["sunset"] + timedelta(minutes = 60)
    sunrise_threshold = solar["sunrise"] - timedelta(minutes = 60)

    # Only take images between sunrise and sunset
    if (utc >= sunrise_threshold.replace(tzinfo = None) and
        utc <= sunset_threshold.replace(tzinfo = None)):

        if not os.path.isdir(config.camera_drive):
            gpio.output(23, gpio.HIGH); return

        # Check free space
        free_space = helpers.remaining_space(config.camera_drive)
        if free_space == None or free_space < 0.1:
            gpio.output(23, gpio.HIGH); return

        try:
            image_dir = os.path.join(config.camera_drive,
                                     utc.strftime("%Y/%m/%d"))
            if not os.path.exists(image_dir): os.makedirs(image_dir)
            image_name = utc.strftime("%Y-%m-%dT%H-%M-%S")
        
            # Set image resolution and capture image
            with picamera.PiCamera() as camera:
                camera.resolution = (1280, 960)
                time.sleep(0.8)

                camera.capture(os.path.join(image_dir, image_name + ".jpg"))
        except: gpio.output(23, gpio.HIGH)

def do_generate_stats(utc):
    """ Generates statistics for the local current day from logged records and
        saves them to the database
    """
    local_time = helpers.utc_to_local(config, utc)

    # -- GET NEW STATS ---------------------------------------------------------
    bounds = helpers.day_bounds_utc(config, local_time, False)
    new_stats = None
    
    try:
        with sqlite3.connect(config.database_path) as database:
            database.row_factory = sqlite3.Row
            cursor = database.cursor()

            cursor.execute(queries.GENERATE_STATS_UTCREPORTS,
                           (bounds[0].strftime("%Y-%m-%d %H:%M:%S"),
                            bounds[1].strftime("%Y-%m-%d %H:%M:%S")))
                            
            new_stats = cursor.fetchone()
    except: gpio.output(23, gpio.HIGH); return

    # -- GET CURRENT STATS -----------------------------------------------------
    cur_stats = analysis.record_for_time(config, local_time, DbTable.LOCALSTATS)
    if cur_stats == False: gpio.output(23, gpio.HIGH); return

    # -- SAVE DATA -------------------------------------------------------------
    free_space = helpers.remaining_space("/")
    if free_space == None or free_space < 0.1:
        gpio.output(23, gpio.HIGH); return

    try:
        with sqlite3.connect(config.database_path) as database:
            cursor = database.cursor()

            # Insert or update depending on status of current statistics
            if cur_stats == None:
                cursor.execute(queries.INSERT_SINGLE_LOCALSTATS,
                    (local_time.strftime("%Y-%m-%d"),
                     new_stats["AirT_Min"], new_stats["AirT_Max"],
                     new_stats["AirT_Avg"], new_stats["RelH_Min"],
                     new_stats["RelH_Max"], new_stats["RelH_Avg"],
                     new_stats["DewP_Min"], new_stats["DewP_Max"],
                     new_stats["DewP_Avg"], new_stats["WSpd_Min"],
                     new_stats["WSpd_Max"], new_stats["WSpd_Avg"],
                     new_stats["WDir_Min"], new_stats["WDir_Max"],
                     new_stats["WDir_Avg"], new_stats["WGst_Min"],
                     new_stats["WGst_Max"], new_stats["WGst_Avg"],
                     new_stats["SunD_Ttl"], new_stats["Rain_Ttl"],
                     new_stats["MSLP_Min"], new_stats["MSLP_Max"],
                     new_stats["MSLP_Avg"], new_stats["ST10_Min"],
                     new_stats["ST10_Max"], new_stats["ST10_Avg"],
                     new_stats["ST30_Min"], new_stats["ST30_Max"],
                     new_stats["ST30_Avg"], new_stats["ST00_Min"],
                     new_stats["ST00_Max"], new_stats["ST00_Avg"]))
                
            else:
                cursor.execute(queries.UPDATE_SINGLE_LOCALSTATS,
                    (new_stats["AirT_Min"], new_stats["AirT_Max"],
                     new_stats["AirT_Avg"], new_stats["RelH_Min"],
                     new_stats["RelH_Max"], new_stats["RelH_Avg"],
                     new_stats["DewP_Min"], new_stats["DewP_Max"],
                     new_stats["DewP_Avg"], new_stats["WSpd_Min"],
                     new_stats["WSpd_Max"], new_stats["WSpd_Avg"],
                     new_stats["WDir_Min"], new_stats["WDir_Max"],
                     new_stats["WDir_Avg"], new_stats["WGst_Min"],
                     new_stats["WGst_Max"], new_stats["WGst_Avg"],
                     new_stats["SunD_Ttl"], new_stats["Rain_Ttl"],
                     new_stats["MSLP_Min"], new_stats["MSLP_Max"],
                     new_stats["MSLP_Avg"], new_stats["ST10_Min"],
                     new_stats["ST10_Max"], new_stats["ST10_Avg"],
                     new_stats["ST30_Min"], new_stats["ST30_Max"],
                     new_stats["ST30_Avg"], new_stats["ST00_Min"],
                     new_stats["ST00_Max"], new_stats["ST00_Avg"],
                     local_time.strftime("%Y-%m-%d")))
            
            database.commit()
    except: gpio.output(23, gpio.HIGH)

# SCHEDULES -------------------------------------------------------------------
def every_minute():
    """ Triggered every minute to generate a report, add it to the database,
        activate the camera and generate statistics
    """
    gpio.output(23, gpio.LOW)
    gpio.output(24, gpio.HIGH)
    utc = datetime.utcnow().replace(second = 0, microsecond = 0)
    time.sleep(0.15)

    # Read CPU temperature before anything else happens. Considered idle temp
    if config.environment_logging == True:
        try:
            global CPUT_value
            CPUT_value = round(CPUTemperature().temperature, 1)
        except: gpio.output(23, gpio.HIGH)

    # Run actions if relevant configuration modifiers are active
    do_log_report(utc)
    if config.camera_logging == True: do_log_camera(utc)
    if config.environment_logging == True: do_log_environment(utc)
    if config.statistic_generation == True: do_generate_stats(utc)

    gpio.output(24, gpio.LOW)

def every_second():
    """ Triggered every second to read sensor values into a list for averaging
    """
    global disable_sampling, WDir_samples, SunD_ticks
    if disable_sampling == True: return

    # -- WIND DIRECTION --------------------------------------------------------
    spi = None

    try:
        spi = Adafruit_GPIO.SPI.SpiDev(0, 0)
        adc = Adafruit_MCP3008.MCP3008(spi = spi)

        # Read sensor value from analog to digital converter
        adc_value = adc.read_adc(1)

        # Convert ADC value to degrees
        if adc_value > 0:
            WDir_degrees = (adc_value - 52) / (976 - 52) * (360 - 0)
            if WDir_degrees < 0 or WDir_degrees >= 359.5: WDir_degrees = 0

            # Add to sample list with timestamp
            WDir_samples.append((datetime.now(), int(round(WDir_degrees))))
        else: gpio.output(23, gpio.HIGH)
    except: gpio.output(23, gpio.HIGH)

    if spi != None: spi.close()

    # -- SUNSHINE DURATION -----------------------------------------------------
    try:
        if gpio.input(22) == True: SunD_ticks += 1
    except: gpio.output(23, gpio.HIGH)

# INTERRUPTS -------------------------------------------------------------------
def do_trigger_wspd(channel):
    global disable_sampling, WSpd_ticks
    if disable_sampling == True: return
    
    WSpd_ticks.append(datetime.now())

def do_trigger_rain(channel):
    global disable_sampling, Rain_ticks
    if disable_sampling == True: return
        
    Rain_ticks += 1


# ENTRY POINT ==================================================================
# -- INIT GPIO AND LEDS --------------------------------------------------------
program_start = datetime.utcnow(); time.sleep(2.5)

try:
    gpio.setwarnings(False); gpio.setmode(gpio.BCM)
    gpio.setup(23, gpio.OUT); gpio.output(23, gpio.LOW)
    gpio.setup(24, gpio.OUT); gpio.output(24, gpio.LOW)
except: helpers.exit_no_light("00")

# -- CHECK INTERNAL DRIVE ------------------------------------------------------
free_space = helpers.remaining_space("/")
if free_space == None or free_space < 1: helpers.exit("01")

# -- CHECK CONFIG --------------------------------------------------------------
if config.load() == False: helpers.exit("02")
if config.validate() == False: helpers.exit("03")

# -- CHECK DATA DIRECTORY ------------------------------------------------------
if not os.path.isdir(config.data_directory):
    try:
        os.makedirs(config.data_directory)
    except: helpers.exit("04")

# -- MAKE DATABASE -------------------------------------------------------------
if not os.path.isfile(config.database_path):
    try:
        with sqlite3.connect(config.database_path) as database:
            cursor = database.cursor()

            cursor.execute(queries.CREATE_UTCREPORTS_TABLE)
            cursor.execute(queries.CREATE_UTCENVIRON_TABLE)
            cursor.execute(queries.CREATE_LOCALSTATS_TABLE)
            database.commit()

    except: helpers.exit("05")

# -- CHECK CAMERA DRIVE --------------------------------------------------------
if config.camera_logging == True:
    if not os.path.isdir(config.camera_drive): helpers.exit("06")

    free_space = helpers.remaining_space(config.camera_drive)
    if free_space == None or free_space < 5: helpers.exit("07")

    # Check camera module is connected
    try:
        with picamera.PiCamera() as camera: pass
    except: helpers.exit("08")

# -- CHECK BACKUP DRVIE --------------------------------------------------------
if config.backups == True:
    if not os.path.isdir(config.backup_drive): helpers.exit("09")

    free_space = helpers.remaining_space(config.backup_drive)
    if free_space == None or free_space < 5: helpers.exit("10")

# -- SET UP SENSORS ------------------------------------------------------------
try:
    gpio.setup(17, gpio.IN, pull_up_down = gpio.PUD_DOWN)
    gpio.setup(27, gpio.IN, pull_up_down = gpio.PUD_DOWN)
    gpio.setup(22, gpio.IN, pull_up_down = gpio.PUD_DOWN)
except: helpers.exit("11")

# -- RUN SUBPROCESSES ----------------------------------------------------------
current_dir = os.path.dirname(os.path.realpath(__file__))

if (config.report_uploading == True or
    config.environment_uploading == True or
    config.statistic_uploading == True or
    config.camera_uploading == True or
    config.integrity_checks == True or
    config.backups == True):

    try:
        subprocess.Popen(["lxterminal -e python3 " + current_dir
                          + "/CAWS_Sup.py"], shell = True)
    except: helpers.exit("12")

if config.local_network_server == True:
    try:
        subprocess.Popen(["lxterminal -e python3 " + current_dir
                          + "/CAWS_Acc.py"], shell = True)
    except: helpers.exit("13")

# -- WAIT FOR MINUTE -----------------------------------------------------------
helpers.init_success()
gpio.output(24, gpio.HIGH)

while True:
    if datetime.utcnow().second != 0:
        gpio.output(23, gpio.HIGH); time.sleep(0.1)
        gpio.output(23, gpio.LOW); time.sleep(0.1)
    else: break

gpio.output(24, gpio.LOW)

# -- START DATA LOGGING --------------------------------------------------------
data_start = datetime.utcnow().replace(second = 0, microsecond = 0)
gpio.add_event_detect(17, gpio.FALLING, callback = do_trigger_wspd,
                      bouncetime = 1)
gpio.add_event_detect(27, gpio.FALLING, callback = do_trigger_rain,
                      bouncetime = 150)

event_scheduler = BlockingScheduler()
event_scheduler.add_job(every_minute, "cron", minute = "0-59")
event_scheduler.add_job(every_second, "cron", second = "0-59")
event_scheduler.start()
