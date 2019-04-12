""" CAWS Data Acquisition Program
      Responsible for logging data parameters and generating statistics
"""

import os
from datetime import datetime, timedelta
import time
from threading import Thread
import sqlite3

import daemon
import RPi.GPIO as gpio
import astral
from apscheduler.schedulers.blocking import BlockingScheduler
import pytz
import picamera

import routines.config as config
import routines.helpers as helpers
from sensors.temperature import Temperature
from sensors.humidity import Humidity
from sensors.wind import Wind
from sensors.direction import Direction
from sensors.sunshine import Sunshine
from sensors.rainfall import Rainfall
from sensors.pressure import Pressure
from sensors.processor import Processor
import routines.frames as frames
from routines.frames import DbTable
from sensors.logtype import LogType
import routines.data as data
import routines.analysis as analysis
import routines.queries as queries


data_start = None
disable_sampling = True

AirT_sensor = Temperature()
ExpT_sensor = Temperature()
RelH_sensor = Humidity()
WSpd_sensor = Wind()
WDir_sensor = Direction()
SunD_sensor = Sunshine()
Rain_sensor = Rainfall()
StaP_sensor = Pressure()
ST10_sensor = Temperature()
ST30_sensor = Temperature()
ST00_sensor = Temperature()
EncT_sensor = Temperature()
CPUT_sensor = Processor()


def operation_log_report(utc):
    """ Reads all sensors, calculates derived and averaged parameters, and
        saves the data to the database
    """
    global disable_sampling, data_start
    frame = frames.DataUtcReport(utc)
    ten_mins_ago = frame.time - timedelta(minutes = 10)
    two_mins_ago = frame.time - timedelta(minutes = 2)
    
    # -- COPY GLOBALS ----------------------------------------------------------
    disable_sampling = True
    if config.WSpd == True: WSpd_sensor.set_pause(True)
    if config.Rain == True: Rain_sensor.set_pause(True)

    # Shift and reset sensor stores to allow data collection to continue
    if config.AirT == True:
        AirT_sensor.shift_store()
        AirT_sensor.reset_store()
    if config.RelH == True:
        RelH_sensor.shift_store()
        RelH_sensor.reset_store()
    if config.WSpd == True:
        WSpd_sensor.shift_store()
        WSpd_sensor.reset_store()
    if config.WDir == True:
        WDir_sensor.shift_store()
        WDir_sensor.reset_store()
    if config.SunD == True:
        SunD_sensor.shift_store()
        SunD_sensor.reset_store()
    if config.Rain == True:
        Rain_sensor.shift_store()
        Rain_sensor.reset_store()
    if config.StaP == True:
        StaP_sensor.shift_store()
        StaP_sensor.reset_store()

    disable_sampling = False
    if config.WSpd == True: WSpd_sensor.set_pause(False)
    if config.Rain == True: Rain_sensor.set_pause(False)

    # -- TEMPERATURES ----------------------------------------------------------
    try:
        # Read each sensor in separate thread to reduce wait
        ExpT_thread = None
        if config.ExpT == True:
            try:
                ExpT_thread = Thread(target = ExpT_sensor.sample, args = ())
                ExpT_thread.start()
            except: helpers.data_error()

        ST10_thread = None
        if config.ST10 == True:
            try:
                ST10_thread = Thread(target = ST10_sensor.sample, args = ())
                ST10_thread.start()
            except: helpers.data_error()

        ST30_thread = None
        if config.ST30 == True:
            try:
                ST30_thread = Thread(target = ST30_sensor.sample, args = ())
                ST30_thread.start()
            except: helpers.data_error()

        ST00_thread = None
        if config.ST00 == True:
            try:
                ST00_thread = Thread(target = ST00_sensor.sample, args = ())
                ST00_thread.start()
            except: helpers.data_error()

        # Wait for all sensors to finish reading
        if config.ExpT == True: ExpT_thread.join()
        if config.ST10 == True: ST10_thread.join()
        if config.ST30 == True: ST30_thread.join()
        if config.ST00 == True: ST00_thread.join()

        # Get read values and check for read errors, for each sensor
        if config.ExpT == True:
            try:
                if ExpT_sensor.get_error() == True: helpers.data_error()
                else:
                    ExpT_value = ExpT_sensor.get_stored()
                    if ExpT_value != None:
                        frame.exposed_temperature = round(ExpT_value, 1)
            except: helpers.data_error()

        if config.ST10 == True:
            try:
                if ST10_sensor.get_error() == True: helpers.data_error()
                else:
                    ST10_value = ST10_sensor.get_stored()
                    if ST10_value != None:
                        frame.soil_temperature_10 = round(ST10_value, 1)
            except: helpers.data_error()

        if config.ST30 == True:
            try:
                if ST30_sensor.get_error() == True: helpers.data_error()
                else:
                    ST10_value = ST30_sensor.get_stored()
                    if ST30_value != None:
                        frame.soil_temperature_30 = round(ST30_value, 1)
            except: helpers.data_error()

        if config.ST00 == True:
            try:
                if ST00_sensor.get_error() == True: helpers.data_error()
                else:
                    ST00_value = ST00_sensor.get_stored()
                    if ST00_value != None:
                        frame.soil_temperature_00 = round(ST00_value, 1)
            except: helpers.data_error()
    except: helpers.data_error()

    # -- AIR TEMPERATURE -------------------------------------------------------
    if config.AirT == True:
        try:
            AirT_value = AirT_sensor.get_shifted()
            if AirT_value != None:
                frame.air_temperature = round(AirT_value, 1)
        except: helpers.data_error()

    # -- RELATIVE HUMIDITY -----------------------------------------------------
    if config.RelH == True:
        try:
            RelH_value = RelH_sensor.get_shifted()
            if RelH_value != None:
                frame.relative_humidity = round(RelH_value, 1)
        except: helpers.data_error()
    
    # -- WIND SPEED ------------------------------------------------------------
    if config.WSpd == True:
        try:
            if two_mins_ago >= data_start:
                WSpd_sensor.prepare_shift(ten_mins_ago)
                WSpd_value = WSpd_sensor.get_shifted(two_mins_ago, False)
                
                if WSpd_value != None:
                    frame.wind_speed = round(WSpd_value, 1)
        except: helpers.data_error()

    # -- WIND DIRECTION --------------------------------------------------------
    if config.WDir == True:
        try:
            if two_mins_ago >= data_start:
                WDir_sensor.prepare_shift(two_mins_ago)
                WDir_value = WDir_sensor.get_shifted()

                if WDir_value != None:
                    frame.wind_direction = WDir_value
        except: helpers.data_error()

    # -- SUNSHINE DURATION -----------------------------------------------------
    if config.SunD == True:
        try:
            SunD_value = SunD_sensor.get_shifted()
            if SunD_value != None:
                frame.sunshine_duration = SunD_value
        except: helpers.data_error()

    # -- RAINFALL --------------------------------------------------------------
    if config.Rain == True:
        try:
            Rain_value = Rain_sensor.get_shifted()
            if Rain_value != None:
                frame.rainfall = round(Rain_value, 3)
        except: helpers.data_error()

    # -- STATION PRESSURE ------------------------------------------------------
    if config.StaP == True:
        try:
            StaP_value = StaP_sensor.get_shifted()
            if StaP_value != None:
                frame.relative_humidity = round(StaP_value, 1)
        except: helpers.data_error()

    # -- DEW POINT -------------------------------------------------------------
    if config.log_DewP == True:
        try:
            DewP_value = data.calculate_dew_point(frame.air_temperature,
                frame.relative_humidity)
            if DewP_value != None: frame.dew_point = round(DewP_value, 1)
        except: helpers.data_error()

    # -- WIND GUST -------------------------------------------------------------
    if config.log_WGst == True:
        try:
            if ten_mins_ago >= data_start:
                WGst_value = WSpd_sensor.get_shifted(ten_mins_ago, True)
                if WGst_value != None:
                    frame.wind_gust = round(WGst_value, 1)
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

    # -- ADD TO DATABASE -------------------------------------------------------
    if config.AirT == True: AirT_sensor.reset_shift()
    if config.ExpT == True: ExpT_sensor.reset_store()
    if config.RelH == True: RelH_sensor.reset_shift()
    if config.SunD == True: SunD_sensor.reset_shift()
    if config.Rain == True: Rain_sensor.reset_shift()
    if config.StaP == True: StaP_sensor.reset_shift()
    if config.ST10 == True: ST10_sensor.reset_store()
    if config.ST30 == True: ST30_sensor.reset_store()
    if config.ST00 == True: ST00_sensor.reset_store()

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

def operation_log_environment(utc):
    """ Reads computer environment sensors and saves the data to the database
    """
    global EncT_sensor, CPUT_sensor
    frame = frames.DataUtcEnviron(utc)

    # -- ENCLOSURE TEMPERATURE -------------------------------------------------
    if config.EncT == True:
        try:
            EncT_sensor.sample()
            if EncT_sensor.get_error() == True: helpers.data_error()

            else:
                EncT_value = EncT_sensor.get_stored()
                if EncT_value != None:
                    frame.enclosure_temperature = round(EncT_value, 1)
        except: helpers.data_error()

    # -- CPU TEMPERATURE -------------------------------------------------------
    try:
        if CPUT_sensor.get_error() == False:
            CPUT_value = CPUT_sensor.get_stored()
            if CPUT_value != None:
                frame.cpu_temperature = round(CPUT_value, 1)
    except: helpers.data_error()

    # -- ADD TO DATABASE -------------------------------------------------------
    EncT_sensor.reset_store()
    CPUT_sensor.reset_store()

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

def operation_generate_stats(utc):
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


def schedule_minute():
    """ Triggered every minute to generate a report and environment report, add
        them to the database, activate the camera and generate statistics
    """
    global CPUT_sensor
    utc = datetime.utcnow().replace(second = 0, microsecond = 0)

    # Reset LEDS and wait to allow schedule_second() to finish
    gpio.output(helpers.DATALEDPIN, gpio.HIGH)
    gpio.output(helpers.ERRORLEDPIN, gpio.LOW)
    time.sleep(0.25)

    # -- CPU TEMPERATURE -------------------------------------------------------
    # Read CPU temperature before anything else happens. Considered idle temp
    try:
        CPUT_sensor.sample()
        if CPUT_sensor.get_error() == True: helpers.data_error()
    except: helpers.data_error()

    # -- RUN OPERATIONS --------------------------------------------------------
    operation_log_report(utc)
    if config.envReport_logging == True: operation_log_environment(utc)
    if config.camera_logging == True: operation_log_camera(utc)
    if config.dayStat_generation == True: operation_generate_stats(utc)
    gpio.output(23, gpio.LOW)

def schedule_second():
    """ Triggered every second to read sensor values into a list for averaging
    """
    global disable_sampling, SunD_sensor, AirT_sensor, RelH_sensor, WDir_sensor
    global StaP_sensor
    utc = datetime.utcnow().replace(microsecond = 0)

    # No sensor reads if sampling is disabled
    if disable_sampling == True: return

    # -- SUNSHINE DURATION -----------------------------------------------------
    if config.SunD == True:
        try:
            SunD_sensor.sample()
            if SunD_sensor.get_error() == True: helpers.data_error()
        except: helpers.data_error()

    # No more sensor reads on 0 second since that is part of the next minute
    if str(utc.second) == "0": return

    # -- AIR TEMPERATURE -------------------------------------------------------
    AirT_thread = None
    if config.AirT == True:
        try:
            AirT_thread = Thread(target = AirT_sensor.sample, args = ())
            AirT_thread.start()
        except: helpers.data_error()

    # -- RELATIVE HUMIDITY -----------------------------------------------------
    if config.RelH == True:
        try:
            RelH_sensor.sample()
            if RelH_sensor.get_error() == True: helpers.data_error()
        except: helpers.data_error()

    # -- WIND DIRECTION --------------------------------------------------------
    if config.WDir == True:
        try:
            WDir_sensor.sample(utc)
            if WDir_sensor.get_error() == True: helpers.data_error()
        except: helpers.data_error()

    # -- STATION PRESSURE ------------------------------------------------------
    if config.StaP == True:
        try:
            StaP_sensor.sample()
            if StaP_sensor.get_error() == True: helpers.data_error()
        except: helpers.data_error()

    # -- AIR TEMPERATURE -------------------------------------------------------
    if config.AirT == True:
        try:
            AirT_thread.join()
            if AirT_sensor.get_error() == True: helpers.data_error()
        except: helpers.data_error()


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
    if config.AirT == True:
        AirT_sensor.setup(LogType.ARRAY, config.AirT_address)
    if config.ExpT == True:
        ExpT_sensor.setup(LogType.VALUE, config.ExpT_address)
    if config.RelH == True: RelH_sensor.setup(LogType.ARRAY)
    if config.WSpd == True: WSpd_sensor.setup(27)
    if config.WDir == True: WDir_sensor.setup(1)
    if config.SunD == True: SunD_sensor.setup(25)
    if config.Rain == True: Rain_sensor.setup(22)
    if config.StaP == True: StaP_sensor.setup(LogType.ARRAY)
    if config.ST10 == True:
        ST10_sensor.setup(LogType.VALUE, config.ST10_address)
    if config.ST30 == True:
        ST30_sensor.setup(LogType.VALUE, config.ST30_address)
    if config.ST00 == True:
        ST00_sensor.setup(LogType.VALUE, config.ST00_address)
    if config.EncT == True:
        EncT_sensor.setup(LogType.VALUE, config.EncT_address)

    # -- WAIT FOR MINUTE -------------------------------------------------------
    event_scheduler = BlockingScheduler()
    event_scheduler.add_job(schedule_minute, "cron", minute = "0-59")
    event_scheduler.add_job(schedule_second, "cron", second = "0-59")

    while datetime.utcnow().second != 0:
        gpio.output(helpers.DATALEDPIN, gpio.HIGH)
        time.sleep(0.1)
        gpio.output(helpers.DATALEDPIN, gpio.LOW)
        time.sleep(0.1)

    # -- START DATA LOGGING ----------------------------------------------------
    data_start = datetime.utcnow().replace(second = 0, microsecond = 0)

    disable_sampling = False
    WSpd_sensor.set_pause(False)
    Rain_sensor.set_pause(False)
    event_scheduler.start()

if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.realpath(__file__))

    with daemon.DaemonContext(working_directory = current_dir):
        entry_point()