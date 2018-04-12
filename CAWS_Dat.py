""" CAWS Data Acquisition Program
      Responsible for measuring and logging data parameters, and for generating
      statistics. This is the entry point for the CAWS software
"""

# DEPENDENCIES -----------------------------------------------------------------
import sys
import subprocess
import os
from datetime import datetime, timedelta
import time
import pytz
from threading import Thread
import math

import sqlite3
import RPi.GPIO as gpio
from apscheduler.schedulers.blocking import BlockingScheduler
import astral
import picamera
from gpiozero import CPUTemperature
import spidev
import bme280
import sht31d

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
start_time = None
disable_sampling = False

wspd_ticks = []
past_wspd_ticks = []
wdir_samples = []
past_wdir_samples = []
sund_ticks = 0
rain_ticks = 0

airt_value = None
expt_value = None
st10_value = None
st30_value = None
st00_value = None
cput_value = None
enct_value = None

# HELPERS ----------------------------------------------------------------------
def do_read_temp(address):
    """ Reads value of specific temperature probe into its global variable
    """
    if not os.path.exists("/sys/bus/w1/devices/" + address):
        gpio.output(23, gpio.HIGH); return

    try:
        with open("/sys/bus/w1/devices/" + address + "/w1_slave", "r") as probe:
            data = probe.readlines()
            temp = int(data[1][data[1].find("t=") + 2:]) / 1000

            # Check for error value
            if temp == -127 or temp == 85: gpio.output(23, gpio.HIGH); return

            # Store value in respective global variable
            if os.path.basename(address) == "28-04167053d6ff":
                global airt_value; airt_value = round(temp, 1)
            elif os.path.basename(address) == "28-0416704a38ff":
                global expt_value; expt_value = round(temp, 1)
            elif os.path.basename(address) == "28-0416705d66ff":
                global st10_value; st10_value = round(temp, 1)
            elif os.path.basename(address) == "28-04167055d5ff":
                global st30_value; st30_value = round(temp, 1)
            elif os.path.basename(address) == "28-0516704dc0ff":
                global st00_value; st00_value = round(temp, 1)
            elif os.path.basename(address) == "28-8000001f88fa":
                global enct_value; enct_value = round(temp, 1)
    except: gpio.output(23, gpio.HIGH)

# OPERATIONS -------------------------------------------------------------------
def do_log_report(utc):
    global wspd_ticks, past_wspd_ticks, wdir_samples, past_wdir_samples
    global sund_ticks, rain_ticks, airt_value, expt_value, st10_value
    global st30_value, st00_value, disable_sampling

    frame = frames.DataUtcReport()
    frame.time = utc
    
    # -- COPY GLOBALS ----------------------------------------------------------
    disable_sampling = True
    new_wspd_ticks = wspd_ticks[:]
    wspd_ticks = []
    new_wdir_samples = wdir_samples[:]
    wdir_samples = []
    new_sund_ticks = sund_ticks
    sund_ticks = 0
    new_rain_ticks = rain_ticks
    rain_ticks = 0
    disable_sampling = False

    # -- TEMPERATURE -----------------------------------------------------------
    try:
        airt_thread = Thread(target = do_read_temp, args = ("28-04167053d6ff",))
        airt_thread.start()
        expt_thread = Thread(target = do_read_temp, args = ("28-0416704a38ff",))
        expt_thread.start()
        st10_thread = Thread(target = do_read_temp, args = ("28-0416705d66ff",))
        st10_thread.start()
        st30_thread = Thread(target = do_read_temp, args = ("28-04167055d5ff",))
        st30_thread.start()
        st00_thread = Thread(target = do_read_temp, args = ("28-0516704dc0ff",))
        st00_thread.start()

        # Read all sensors in separate threads to reduce wait time
        airt_thread.join(); frame.air_temperature = airt_value
        expt_thread.join(); frame.exposed_temperature = expt_value
        st10_thread.join(); frame.soil_temperature_10 = st10_value
        st30_thread.join(); frame.soil_temperature_30 = st30_value
        st00_thread.join(); frame.soil_temperature_00 = st00_value
    except: gpio.output(23, gpio.HIGH)

    airt_value = None; expt_value = None; st10_value = None
    st30_value = None; st00_value = None

    # -- RELATIVE HUMIDITY -----------------------------------------------------
    try:
        frame.relative_humidity = round(
            sht31d.SHT31(address = 0x44).read_humidity(), 1)
    except: gpio.output(23, gpio.HIGH)

    # -- STATION PRESSURE ------------------------------------------------------
    try:
        stap_sensor = bme280.BME280(p_mode = bme280.BME280_OSAMPLE_8)

        # Temperature must be read first or pressure will not return
        discard_stap_temp = stap_sensor.read_temperature()
        frame.station_pressure = round(stap_sensor.read_pressure() / 100, 1)
    except: gpio.output(23, gpio.HIGH)
        
    # -- WIND SPEED ------------------------------------------------------------
    ten_mins_ago = frame.time - timedelta(minutes = 10)
    
    try:
        past_wspd_ticks.extend(new_wspd_ticks)

        # Remove ticks older than 10 minutes
        for tick in list(past_wspd_ticks):
            if tick < ten_mins_ago: past_wspd_ticks.remove(tick)

        # Calculate wind speed only if 10 minutes of data is available
        if ten_mins_ago >= start_time:
            frame.wind_speed = round((len(past_wspd_ticks) * 2.5) / 600, 1)
    except: gpio.output(23, gpio.HIGH)

    # -- WIND DIRECTION --------------------------------------------------------
    try:
        past_wdir_samples.extend(new_wdir_samples)

        # Remove samples older than 10 minutes
        for sample in list(past_wdir_samples):
            if sample[0] < ten_mins_ago: past_wdir_samples.remove(sample)

        # Calculate wind direction only if there is positive wind speed
        if frame.wind_speed != None:
            if frame.wind_speed > 0 and len(past_wdir_samples) > 0:
                wdir_total = 0
                for i in past_wdir_samples: wdir_total += i[1]

                frame.wind_direction = int(round(wdir_total
                                                 / len(past_wdir_samples)))
    except: gpio.output(23, gpio.HIGH)

    # -- WIND GUST -------------------------------------------------------------
    try:
        # Calculate wind gust if there is positive wind speed
        if frame.wind_speed != None:
            if frame.wind_speed > 0:
                wgst_value = 0

                # Iterate over each second in three second samples
                for second in range(0, 598):
                    wgst_start = ten_mins_ago + timedelta(seconds = second)
                    wgst_end = wgst_start + timedelta(seconds = 3)
                    ticks_in_wgst_sample = 0

                    # Calculate three second average wind speed
                    for tick in past_wspd_ticks:
                        if tick >= wgst_start and tick < wgst_end:
                            ticks_in_wgst_sample += 1

                    wgst_sample = (ticks_in_wgst_sample * 2.5) / 3
                    if wgst_sample > wgst_value: wgst_value = wgst_sample
                    
                frame.wind_gust = round(wgst_value, 1)
    except: gpio.output(23, gpio.HIGH)

    # -- SUNSHINE DURATION -----------------------------------------------------
    try:
        frame.sunshine_duration = new_sund_ticks
    except: gpio.output(23, gpio.HIGH)

    # -- RAINFALL --------------------------------------------------------------
    try:
        frame.rainfall = new_rain_ticks * 0.254
    except: gpio.output(23, gpio.HIGH)

    # -- DEW POINT -------------------------------------------------------------
    try:
        if frame.air_temperature != None and frame.relative_humidity != None:
            dewp_a = 0.4343 * math.log(frame.relative_humidity / 100)
            dewp_b = ((8.082 - frame.air_temperature / 556.0)
                      * frame.air_temperature)
            dewp_c = dewp_a + (dewp_b) / (256.1 + frame.air_temperature)
            dewp_d = math.sqrt((8.0813 - dewp_c) ** 2 - (1.842 * dewp_c))
            
            frame.dew_point = round(278.04 * ((8.0813 - dewp_c) - dewp_d), 1)
    except: gpio.output(23, gpio.HIGH)

    # -- MEAN SEA LEVEL PRESSURE -----------------------------------------------
    try:
        if (frame.station_pressure != None and
            frame.air_temperature != None and
            frame.dew_point != None):

            pmsl_a = 6.11 * 10 ** ((7.5 * frame.dew_point) / (237.3 +
                                                             frame.dew_point))
            pmsl_b = (9.80665 / 287.3) * config.caws_elevation
            pmsl_c = ((0.0065 * config.caws_elevation) / 2) 
            pmsl_d = frame.air_temperature + 273.15 + pmsl_c + pmsl_a * 0.12
            
            frame.mean_sea_level_pressure = round(frame.station_pressure
                                                  *math.exp(pmsl_b / pmsl_d), 1)
    except: gpio.output(23, gpio.HIGH)

    # -- PRESSURE TENDENCY -----------------------------------------------------
    try:
        if frame.station_pressure != None:
            three_hours_ago = frame.time - timedelta(hours = 3)
            record_then = analysis.record_for_time(config, three_hours_ago,
                                                   DbTable.UTCREPORTS)

            # Calculate difference between pressure 3 hours ago
            if record_then != False:
                if record_then != None:
                    pten_value = round(frame.station_pressure
                                       - record_then["PTen"], 1)
                    frame.pressure_tendency = pten_value
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
    global enct_value, cput_value
    frame = frames.DataUtcEnviron()
    frame.time = utc

    # -- ENCLOSURE TEMPERATURE -------------------------------------------------
    try:
        do_read_temp("28-8000001f88fa")
        frame.enclosure_temperature = enct_value
    except: gpio.output(23, gpio.HIGH)

    # -- CPU TEMPERATURE -------------------------------------------------------
    try:
        frame.cpu_temperature = cput_value
    except: gpio.output(23, gpio.HIGH)

    enct_value = None
    cput_value = None

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
        
            # Set image annotation and capture image
            with picamera.PiCamera() as camera:
                camera.resolution = (1280, 960)
                camera.annotate_background = picamera.Color("black")
                camera.annotate_text_size = 24
                time.sleep(0.8)

                local_time = helpers.utc_to_local(config, utc)
                camera.annotate_text = ("AWS Camera " + local_time.strftime(
                                        "on %d/%m/%Y at %H:%M:%S"))
                camera.capture(os.path.join(image_dir, image_name + ".jpg"))
        except: gpio.output(23, gpio.HIGH)

def do_generate_stats(utc):
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
                     new_stats["min(AirT)"], new_stats["max(AirT)"],
                     new_stats["avg(AirT)"], new_stats["min(RelH)"],
                     new_stats["max(RelH)"], new_stats["avg(RelH)"],
                     new_stats["min(DewP)"], new_stats["max(DewP)"],
                     new_stats["avg(DewP)"], new_stats["min(WSpd)"],
                     new_stats["max(WSpd)"], new_stats["avg(WSpd)"],
                     new_stats["min(WDir)"], new_stats["max(WDir)"],
                     new_stats["avg(WDir)"], new_stats["min(WGst)"],
                     new_stats["max(WGst)"], new_stats["avg(WGst)"],
                     new_stats["sum(SunD)"], new_stats["sum(Rain)"],
                     new_stats["min(MSLP)"], new_stats["max(MSLP)"],
                     new_stats["avg(MSLP)"], new_stats["min(ST10)"],
                     new_stats["max(ST10)"], new_stats["avg(ST10)"],
                     new_stats["min(ST30)"], new_stats["max(ST30)"],
                     new_stats["avg(ST30)"], new_stats["min(ST00)"],
                     new_stats["max(ST00)"], new_stats["avg(ST00)"]))
                
            else:
                cursor.execute(queries.UPDATE_SINGLE_LOCALSTATS,
                    (new_stats["min(AirT)"], new_stats["max(AirT)"],
                     new_stats["avg(AirT)"], new_stats["min(RelH)"],
                     new_stats["max(RelH)"], new_stats["avg(RelH)"],
                     new_stats["min(DewP)"], new_stats["max(DewP)"],
                     new_stats["avg(DewP)"], new_stats["min(WSpd)"],
                     new_stats["max(WSpd)"], new_stats["avg(WSpd)"],
                     new_stats["min(WDir)"], new_stats["max(WDir)"],
                     new_stats["avg(WDir)"], new_stats["min(WGst)"],
                     new_stats["max(WGst)"], new_stats["avg(WGst)"],
                     new_stats["sum(SunD)"], new_stats["sum(Rain)"],
                     new_stats["min(MSLP)"], new_stats["max(MSLP)"],
                     new_stats["avg(MSLP)"], new_stats["min(ST10)"],
                     new_stats["max(ST10)"], new_stats["avg(ST10)"],
                     new_stats["min(ST30)"], new_stats["max(ST30)"],
                     new_stats["avg(ST30)"], new_stats["min(ST00)"],
                     new_stats["max(ST00)"], new_stats["avg(ST00)"],
                     local_time.strftime("%Y-%m-%d")))
            
            database.commit()
    except: gpio.output(23, gpio.HIGH)

# SCHEDULED FUNCTIONS ----------------------------------------------------------
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
            global cput_value
            cput_value = round(CPUTemperature().temperature, 1)
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
    global disable_sampling, wdir_samples, sund_ticks
    if disable_sampling == True: return

    # -- WIND DIRECTION --------------------------------------------------------
    spi_bus = None

    try:
        spi_bus = spidev.SpiDev()
        spi_bus.open(0, 0)

        # Read rotation value from analog to digital converter
        wdir_data = spi_bus.xfer2([1, (8 + 1) << 4, 0])
        adc_value = ((wdir_data[1] & 3) << 8) + wdir_data[2]

        # Convert ADC value to degrees
        if adc_value > 0:
            wdir_degrees = (adc_value - 52) / (976 - 52) * (360 - 0)
            if wdir_degrees < 0 or wdir_degrees >= 359.5: wdir_degrees = 0

            # Add offset from north to compensate for non-north mounting
            wdir_degrees -= 148
            if wdir_degrees >= 360: wdir_degrees -= 360
            elif wdir_degrees < 0: wdir_degrees += 360

            # Add to sample list with timestamp
            wdir_samples.append((datetime.now(), int(round(wdir_degrees))))
    except: gpio.output(23, gpio.HIGH)

    if spi_bus != None: spi_bus.close()

    # -- SUNSHINE DURATION -----------------------------------------------------
    try:
        if gpio.input(22) == True: sund_ticks += 1
    except: gpio.output(23, gpio.HIGH)

# INTERRUPT SERVICE ------------------------------------------------------------
def do_trigger_wspd(channel):
    global disable_sampling, wspd_ticks
    if disable_sampling == True: return
    
    wspd_ticks.append(datetime.now())

def do_trigger_rain(channel):
    global disable_sampling, rain_ticks
    if disable_sampling == True: return
        
    rain_ticks += 1


# ENTRY POINT ==================================================================
# -- INIT GPIO AND LEDS --------------------------------------------------------
time.sleep(2.5)

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
    
# -- CHECK GRAPH DIRECTORY -----------------------------------------------------
if (config.day_graph_generation == True or
    config.month_graph_generation == True or
    config.year_graph_generation == True):

    if not os.path.isdir(config.graph_directory):
        try:
            os.makedirs(config.graph_directory)
        except: helpers.exit("11")


# -- RUN SUBPROCESSES ----------------------------------------------------------
current_dir = os.path.dirname(os.path.realpath(__file__))

if (config.day_graph_generation == True or
    config.month_graph_generation == True or
    config.year_graph_generation == True or
    config.report_uploading == True or
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
start_time = datetime.utcnow().replace(second = 0, microsecond = 0)
gpio.setup(17, gpio.IN, pull_up_down = gpio.PUD_DOWN)
gpio.add_event_detect(17, gpio.FALLING, callback = do_trigger_wspd,
                      bouncetime = 1)
gpio.setup(27, gpio.IN, pull_up_down = gpio.PUD_DOWN)
gpio.add_event_detect(27, gpio.FALLING, callback = do_trigger_rain,
                      bouncetime = 150)
gpio.setup(22, gpio.IN, pull_up_down = gpio.PUD_DOWN)

event_scheduler = BlockingScheduler()
event_scheduler.add_job(every_minute, "cron", minute = "0-59")
event_scheduler.add_job(every_second, "cron", second = "0-59")
event_scheduler.start()
