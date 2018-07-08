""" CAWS Data Support Program
      Responsible for generating various data products, uploading data to
      internet services, and generating backups and database metrics
"""

# DEPENDENCIES -----------------------------------------------------------------
from datetime import datetime
import os
import threading
import requests

from apscheduler.schedulers.blocking import BlockingScheduler

import analysis
import helpers
from frames import DbTable
from config import ConfigData

# MESSAGE ----------------------------------------------------------------------
print("--- Custom Automatic Weather Station ---")
print("Program: Support Sub-System")
print("Author:  Henry Hunt")
print("Version: 4C.1 (July 2018)")
print("")
print("----------- DO NOT TERMINATE -----------")

# GLOBAL VARIABLES -------------------------------------------------------------
config = None

is_processing_data = False
is_processing_camera = True
data_queue = []
camera_queue = []

# OPERATIONS -------------------------------------------------------------------
def do_upload_data(data):
    global data_queue, is_processing_data
    try: data_queue.append(data)
    except: pass

    # Only process queue if not already being processed
    if is_processing_data == False and len(data_queue) > 0:
        threading.Thread(target = do_process_data).start()

def do_upload_camera(image_path):
    global camera_queue, is_processing_camera
    try: camera_queue.append(image_path)
    except: pass

    # Only process queue if not already being processed
    if not is_processing_camera and len(camera_queue) > 0:
        threading.Thread(target = do_process_camera).start()

def do_process_data():
    global data_queue, camera_queue, is_processing_data, is_processing_camera
    is_processing_data = True

    for data in list(data_queue):
        if data[0] == False or data[0] == None: data_has_report = 0
        else: data_has_report = 1
        if data[1] == False or data[1] == None: data_has_stat = 0
        else: data_has_stat = 1
        if data[2] == False or data[2] == None: data_has_environ = 0
        else: data_has_environ = 1

        data_new = {
            "pass": "caws-warwick",

            "has_report": data_has_report,
            "has_stat": data_has_stat,
            "has_environ": data_has_environ
        }

        if data_has_report == 1:
            data_new["RTime"] = helpers.none_to_null(data[0]["Time"]).replace(" ", "+"),
            data_new["AirT"] = helpers.none_to_null(data[0]["AirT"]),
            data_new["ExpT"] = helpers.none_to_null(data[0]["ExpT"]),
            data_new["RelH"] = helpers.none_to_null(data[0]["RelH"]),
            data_new["DewP"] = helpers.none_to_null(data[0]["DewP"]),
            data_new["WSpd"] = helpers.none_to_null(data[0]["WSpd"]),
            data_new["WDir"] = helpers.none_to_null(data[0]["WDir"]),
            data_new["WGst"] = helpers.none_to_null(data[0]["WGst"]),
            data_new["SunD"] = helpers.none_to_null(data[0]["SunD"]),
            data_new["Rain"] = helpers.none_to_null(data[0]["Rain"]),
            data_new["StaP"] = helpers.none_to_null(data[0]["StaP"]),
            data_new["PTen"] = helpers.none_to_null(data[0]["PTen"]),
            data_new["MSLP"] = helpers.none_to_null(data[0]["MSLP"]),
            data_new["ST10"] = helpers.none_to_null(data[0]["ST10"]),
            data_new["ST30"] = helpers.none_to_null(data[0]["ST30"]),
            data_new["ST00"] = helpers.none_to_null(data[0]["ST00"]),

        if data_has_stat == 1:
            data_new["Date"] = helpers.none_to_null(data[1]["Date"]),
            data_new["AirT_Min"] = helpers.none_to_null(data[1]["AirT_Min"]),
            data_new["AirT_Max"] = helpers.none_to_null(data[1]["AirT_Max"]),
            data_new["AirT_Avg"] = helpers.none_to_null(data[1]["AirT_Avg"]),
            data_new["RelH_Min"] = helpers.none_to_null(data[1]["RelH_Min"]),
            data_new["RelH_Max"] = helpers.none_to_null(data[1]["RelH_Max"]),
            data_new["RelH_Avg"] = helpers.none_to_null(data[1]["RelH_Avg"]),
            data_new["DewP_Min"] = helpers.none_to_null(data[1]["DewP_Min"]),
            data_new["DewP_Max"] = helpers.none_to_null(data[1]["DewP_Max"]),
            data_new["DewP_Avg"] = helpers.none_to_null(data[1]["DewP_Avg"]),
            data_new["WSpd_Min"] = helpers.none_to_null(data[1]["WSpd_Min"]),
            data_new["WSpd_Max"] = helpers.none_to_null(data[1]["WSpd_Max"]),
            data_new["WSpd_Avg"] = helpers.none_to_null(data[1]["WSpd_Avg"]),
            data_new["WDir_Min"] = helpers.none_to_null(data[1]["WDir_Min"]),
            data_new["WDir_Max"] = helpers.none_to_null(data[1]["WDir_Max"]),
            data_new["WDir_Avg"] = helpers.none_to_null(data[1]["WDir_Avg"]),
            data_new["WGst_Min"] = helpers.none_to_null(data[1]["WGst_Min"]),
            data_new["WGst_Max"] = helpers.none_to_null(data[1]["WGst_Max"]),
            data_new["WGst_Avg"] = helpers.none_to_null(data[1]["WGst_Avg"]),
            data_new["SunD_Ttl"] = helpers.none_to_null(data[1]["SunD_Ttl"]),
            data_new["Rain_Ttl"] = helpers.none_to_null(data[1]["Rain_Ttl"]),
            data_new["MSLP_Min"] = helpers.none_to_null(data[1]["MSLP_Min"]),
            data_new["MSLP_Max"] = helpers.none_to_null(data[1]["MSLP_Max"]),
            data_new["MSLP_Avg"] = helpers.none_to_null(data[1]["MSLP_Avg"]),
            data_new["ST10_Min"] = helpers.none_to_null(data[1]["ST10_Min"]),
            data_new["ST10_Max"] = helpers.none_to_null(data[1]["ST10_Max"]),
            data_new["ST10_Avg"] = helpers.none_to_null(data[1]["ST10_Avg"]),
            data_new["ST30_Min"] = helpers.none_to_null(data[1]["ST30_Min"]),
            data_new["ST30_Max"] = helpers.none_to_null(data[1]["ST30_Max"]),
            data_new["ST30_Avg"] = helpers.none_to_null(data[1]["ST30_Avg"]),
            data_new["ST00_Min"] = helpers.none_to_null(data[1]["ST00_Min"]),
            data_new["ST00_Max"] = helpers.none_to_null(data[1]["ST00_Max"]),
            data_new["ST00_Avg"] = helpers.none_to_null(data[1]["ST00_Avg"]),

        if data_has_environ == 1:
            data_new["ETime"] = helpers.none_to_null(data[2]["Time"]).replace(" ", "+"),
            data_new["EncT"] = helpers.none_to_null(data[2]["EncT"]),
            data_new["CPUT"] = helpers.none_to_null(data[2]["CPUT"])

        try:
            request = requests.post(config.remote_sql_server, data_new, timeout = 5)

            if request.text == "0": data_queue.remove(data)
            else: break
        except: break

    is_processing_data = False

def do_process_camera():
    pass

# SCHEDULES --------------------------------------------------------------------
def every_minute():
    utc = datetime.utcnow().replace(second = 0, microsecond = 0)
    local_time = helpers.utc_to_local(config, utc)

    # Add data to upload queue
    report = analysis.record_for_time(config, utc, DbTable.UTCREPORTS)
    stat = analysis.record_for_time(config, local_time, DbTable.LOCALSTATS)
    environ = analysis.record_for_time(config, utc, DbTable.UTCENVIRON)

    if ((report != False and report != None) or
        (stat != False and stat != None) or
        (environ != False and environ != None)):

        do_upload_data((report, stat, environ))

    # Add camera to upload queue
    image_path = os.path.join(config.camera_drive, utc.strftime("%Y/%m/%d"),
                              utc.strftime("%Y-%m-%dT%H-%M-%S"))
    if os.path.isfile(image_path): do_upload_camera(image_path)
    

# ENTRY POINT ==================================================================
# -- LOAD CONFIG ---------------------------------------------------------------
config = ConfigData()
if config.load() == False: sys.exit(1)
if config.validate() == False: sys.exit(1)

# -- START SCHEDULES -----------------------------------------------------------
event_scheduler = BlockingScheduler()
event_scheduler.add_job(every_minute, "cron", minute = "0-59", second = 8)
event_scheduler.start()
