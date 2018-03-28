""" ICAWS Data Acquisition Program
      Responsible for measuring and logging data parameters, and for generating
      statistics. This is the entry point for the ICAWS software
"""

# DEPENDENCIES -----------------------------------------------------------------
import sys
import subprocess
import os
from datetime import datetime, timedelta
import time
import picamera
import RPi.GPIO as gpio
import pytz

import sqlite3
from apscheduler.schedulers.blocking import BlockingScheduler
import astral

from config import ConfigData
import helpers

# GLOBAL VARIABLES -------------------------------------------------------------
print("          ICAWS Data Acquisition Software, Version 4 - 2018, Henry Hunt"
    + "\n*********************************************************************"
    + "***********\n\n                          DO NOT TERMINATE THIS PROGRAM")
time.sleep(2.5)

config = ConfigData()
start_time = None
disable_interrupts = False

wspd_ticks = []
past_wspd_ticks = []
wdir_samples = []
past_wdir_samples = []
rain_ticks = 0
sund_ticks = 0

tair_temp_value = None
expt_temp_value = None
st10_temp_value = None
st30_temp_value = None
st00_temp_value = None
enct_temp_value = None

# HELPERS ----------------------------------------------------------------------
def do_read_temp(probe):
    pass

# OPERATIONS -------------------------------------------------------------------
def do_log_report():
    pass

def do_log_environment():
    pass

def do_log_camera():
    cur_minute = str(datetime.utcnow().minute)

    # Only run every five minutes
    if cur_minute.endswith("0") or cur_minute.endswith("5"):
        location = astral.Location(("", "", float(config.icaws_latitude),
                                    float(sonfig.icaws_longitude), "UTC", 0))
        sun = location.sun(date = datetime.utcnow(), local = True)
        
        set_threshold = sun["sunset"] + timedelta(minutes = 60)
        rise_threshold = sun["sunrise"] - timedelta(minutes = 60)

        # Only take images between sunrise and sunset
        if (datetime.now(pytz.utc) >= rise_threshold and
            datetime.now(pytz.utc) <= set_threshold):

            if not os.path.isdir(config.camera_drive): return
            free_space = helpers.remaining_space(config.camera_drive)
            if free_space == None or free_space < 5: return

            try:
                image_dir = os.path.join(
                    config.camera_drive, datetime.utcnow()
                    .strftime("%Y/%m/%d/"))
                if not os.path.exists(image_dir): os.makedirs(image_dir)
                image_name = (datetime.utcnow().strftime("%Y-%m-%dT%H-%M-%S")
                              + ".jpg")
            
                # Set image annotation and capture image
                local_time = datetime.now(pytz.timezone(config.icaws_time_zone))
                annotation = ("ICAWS Camera 1 " + local_time.strftime(
                    "on %d/%m/%Y at %H:%M:%S"))
                camera.annotate_text = annotation
                camera.capture(os.path.join(image_dir, image_name))
            except: return

def do_generate_stats():
    pass

# SCHEDULED FUNCTIONS ----------------------------------------------------------
def every_minute():
    """ Triggered every minute to generate a report, add it to the database,
        activate the camera and generate statistics
    """
    time.sleep(0.1)
    gpio.output(24, gpio.HIGH)

    do_log_report()
    if config.environment_logging == True: do_log_environment()
    if config.camera_logging == True: do_log_camera()
    if config.statistic_generation == True: do_generate_stats()
    time.sleep(0.5)

    gpio.output(24, gpio.LOW)

def every_second():
    """ Triggered every second to read sensor values into a list for averaging
    """
    pass

# INTERRUPT SERVICE ------------------------------------------------------------
def do_trigger_wspd():
    pass

def do_trigger_rain():
    pass


# ENTRY POINT ==================================================================
# -- INIT GPIO AND LEDS --------------------------------------------------------
try:
    gpio.setwarnings(False); gpio.setmode(gpio.BCM)

    gpio.setup(23, gpio.OUT); gpio.output(23, gpio.LOW)
    gpio.setup(24, gpio.OUT); gpio.output(24, gpio.LOW)
except: helpers.exit_no_light("00")

# -- CHECK INTERNAL STORAGE ----------------------------------------------------
free_space = helpers.remaining_space("/")
if free_space == None or free_space < 1: helpers.exit("01")

config_load = config.load()
if config_load == None: helpers.exit("02")

# -- CHECK DATA DIRECTORY ------------------------------------------------------
if config.data_directory == None: helpers.exit("03")
if not os.path.isdir(config.data_directory):
    try:
        os.makedirs(config.data_directory)
    except: helpers.exit("04")

# -- MAKE DATABASE -------------------------------------------------------------
if not os.path.isfile(config.database_path):
    try:
        with sqlite3.connect(config.database_path) as database:
            cursor = database.cursor()
            cursor.execute("CREATE TABLE utcReports (" +
                                "Time TEXT PRIMARY KEY NOT NULL," +
                                "AirT REAL, ExpT REAL, RelH REAL," +
                                "DewP REAL, WSpd REAL, WDir REAL," +
                                "WGst REAL, SunD REAL, Rain REAL," +
                                "StaP REAL, PTen REAL, MSLP REAL," +
                                "ST10 REAL, ST30 REAL, ST00 REAL" +
                            ")")
            cursor.execute("CREATE TABLE utcEnviron (" +
                                "Time TEXT PRIMARY KEY NOT NULL," +
                                "EncT REAL, CPUT REAL" +
                            ")")
            cursor.execute("CREATE TABLE localStats (" +
                                "Date TEXT PRIMARY KEY NOT NULL," +
                                "AirT_Min REAL, AirT_Max REAL," +
                                "AirT_Avg REAL, RelH_Min REAL," +
                                "RelH_Max REAL, RelH_Avg REAL," +
                                "DewP_Min REAL, DewP_Max REAL," +
                                "DewP_Avg REAL, WSpd_Max REAL," +
                                "WSpd_Avg REAL, WDir_Avg REAL," +
                                "WGst_Max REAL, WGst_Avg REAL," +
                                "SunD_Ttl REAL, Rain_Ttl REAL," +
                                "MSLP_Min REAL, MSLP_Max REAL," +
                                "MSLP_Avg REAL, TS10_Min REAL," +
                                "TS10_Max REAL, TS10_Avg REAL," +
                                "TS30_Min REAL, TS30_Max REAL," +
                                "TS30_Avg REAL, TS00_Min REAL," +
                                "TS00_Max REAL, TS00_Avg REAL" +
                            ")")
            database.commit()
    except: helpers.exit("05")

# -- CHECK TIME ZONE -----------------------------------------------------------
if (config.camera_logging == True or
    config.statistic_generation == True or
    config.day_graph_generation == True or
    config.month_graph_generation == True or
    config.year_graph_generation == True or
    config.integrity_checks == True or
    config.local_network_server == True or
    config.backups == True):

    if config.icaws_time_zone == None: helpers.exit("06")
    if not config.icaws_time_zone in pytz.all_timezones: helpers.exit("07")

# -- CHECK CAMERA DRIVE --------------------------------------------------------
if config.camera_logging == True:
    if config.camera_drive == None: helpers.exit("08")
    if not os.path.isdir(config.camera_drive): helpers.exit("09")

    free_space = helpers.remaining_space(config.camera_drive)
    if free_space == None or free_space < 5: helpers.exit("10")

    # Check latitude and longitude are correctly supplied
    if config.icaws_latitude == None or config.icaws_longitude == None:
        helpers.exit("11")

    try:
        latitude = float(config.icaws_latitude)
        longitude = float(config.icaws_longitude)
    except: helpers.exit("12")

    # Check camera is connected
    try:
        with picamera.PiCamera() as camera: pass
    except: helpers.exit("13")

# -- CHECK BACKUP DRVIE --------------------------------------------------------
if config.backups == True:
    if config.backup_drive == None: helpers.exit("14")
    if not os.path.isdir(config.backup_drive): helpers.exit("15")

    free_space = helpers.remaining_space(config.backup_drive)
    if free_space == None or free_space < 5: helpers.exit("16")

# -- CHECK GRAPHERS ------------------------------------------------------------
if (config.statistic_generation == False and
    (config.month_graph_generation == True or
     config.year_graph_generation == True)):

    helpers.exit("17")
    
# -- CHECK GRAPH DIRECTORY -----------------------------------------------------
if (config.day_graph_generation == True or
    config.month_graph_generation == True or
    config.year_graph_generation == True):

    if not os.path.isdir(config.graph_directory):
        try:
            os.makedirs(config.graph_directory)
        except: helpers.exit("18")

# -- CHECK UPLOADERS -----------------------------------------------------------
if ((config.environment_logging == False and
     config.environment_uploading == True) or
    (config.camera_logging == False and
     config.camera_uploading == True) or
    (config.statistic_generation == False and
     config.statistic_uploading == True) or
    (config.day_graph_generation == False and
     config.day_graph_uploading == True) or
    (config.month_graph_generation == False and
     config.month_graph_uploading == True) or
    (config.year_graph_generation == False and
     config.year_graph_uploading == True)):

    helpers.exit("19")

# -- CHECK UPLOAD ENDPOINTS ----------------------------------------------------
if (config.report_uploading == True or
    config.environment_uploading == True or
    config.statistic_uploading == True):

    if config.remote_sql_server == None: helpers.exit("20")

if (config.camera_uploading == True or
    config.day_graph_uploading == True or
    config.month_graph_uploading == True or
    config.year_graph_uploading == True):

    if (config.remote_ftp_server == None or
        config.remote_ftp_username == None or
        config.remote_ftp_password == None):

        helpers.exit("21")


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
                          + "icaws_support.py"], shell = True)
    except: helpers.exit("22")

if config.local_network_server == True:
    try:
        subprocess.Popen(["lxterminal -e python3 " + current_dir
                          + "icaws_access.py"], shell = True)
    except: helpers.exit("23")

# -- WAIT FOR MINUTE -----------------------------------------------------------
helpers.init_success()
gpio.output(24, gpio.HIGH)

while True:
    if datetime.utcnow().second != 0:
        gpio.output(23, gpio.HIGH)
        time.sleep(0.1)
        gpio.output(23, gpio.LOW)
        time.sleep(0.1)
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
