""" CAWS Data Support Program
      Responsible for uploading data to various internet services
"""

# DEPENDENCIES -----------------------------------------------------------------
from datetime import datetime
import os
import threading
import requests
from collections import deque
import ftplib

import daemon
from apscheduler.schedulers.blocking import BlockingScheduler

import analysis
import helpers
from frames import DbTable
from config import ConfigData

# GLOBAL VARIABLES -------------------------------------------------------------
config = ConfigData()

data_queue = deque(maxlen = 7200)
camera_queue = deque(maxlen = 1000)
is_processing_data = False
is_processing_camera = False

# HELPERS ----------------------------------------------------------------------
def none_to_null(value):
    return "NULL" if value == None else value

# OPERATIONS -------------------------------------------------------------------
def do_process_data_queue():
    global data_queue, is_processing_data
    if is_processing_data == True: return
    else: is_processing_data = True

    # Process while there are items in the queue
    while len(data_queue) > 0:
        data = data_queue.popleft()
        has_report = False if data[0] == False or data[0] == None else True
        has_envReport = False if data[1] == False or data[1] == None else True
        has_dayStat = False if data[2] == False or data[2] == None else True

        if (has_report == False and has_envReport == False
            and has_dayStat == False): continue

        to_upload = {
            "has_report": 1 if has_report == True else 0,
            "has_envReport": 1 if has_envReport == True else 0,
            "has_dayStat": 1 if has_dayStat == True else 0
        }

        # Add report data to data to upload
        if has_report == True:
            to_upload["Time"] = data[0]["Time"]
            to_upload["AirT"] = none_to_null(data[0]["AirT"])
            to_upload["ExpT"] = none_to_null(data[0]["ExpT"])
            to_upload["RelH"] = none_to_null(data[0]["RelH"])
            to_upload["DewP"] = none_to_null(data[0]["DewP"])
            to_upload["WSpd"] = none_to_null(data[0]["WSpd"])
            to_upload["WDir"] = none_to_null(data[0]["WDir"])
            to_upload["WGst"] = none_to_null(data[0]["WGst"])
            to_upload["SunD"] = none_to_null(data[0]["SunD"])
            to_upload["Rain"] = none_to_null(data[0]["Rain"])
            to_upload["StaP"] = none_to_null(data[0]["StaP"])
            to_upload["MSLP"] = none_to_null(data[0]["MSLP"])
            to_upload["ST10"] = none_to_null(data[0]["ST10"])
            to_upload["ST30"] = none_to_null(data[0]["ST30"])
            to_upload["ST00"] = none_to_null(data[0]["ST00"])

        # Add environment data to data to upload
        if has_envReport == True:
            to_upload["Time"] = data[1]["Time"]
            to_upload["EncT"] = none_to_null(data[1]["EncT"])
            to_upload["CPUT"] = none_to_null(data[1]["CPUT"])

        # Add statistic data to data to upload
        if has_dayStat == True:
            to_upload["Date"] = data[2]["Date"],
            to_upload["AirT_Min"] = none_to_null(data[2]["AirT_Min"])
            to_upload["AirT_Max"] = none_to_null(data[2]["AirT_Max"])
            to_upload["AirT_Avg"] = none_to_null(data[2]["AirT_Avg"])
            to_upload["RelH_Min"] = none_to_null(data[2]["RelH_Min"])
            to_upload["RelH_Max"] = none_to_null(data[2]["RelH_Max"])
            to_upload["RelH_Avg"] = none_to_null(data[2]["RelH_Avg"])
            to_upload["DewP_Min"] = none_to_null(data[2]["DewP_Min"])
            to_upload["DewP_Max"] = none_to_null(data[2]["DewP_Max"])
            to_upload["DewP_Avg"] = none_to_null(data[2]["DewP_Avg"])
            to_upload["WSpd_Min"] = none_to_null(data[2]["WSpd_Min"])
            to_upload["WSpd_Max"] = none_to_null(data[2]["WSpd_Max"])
            to_upload["WSpd_Avg"] = none_to_null(data[2]["WSpd_Avg"])
            to_upload["WDir_Min"] = none_to_null(data[2]["WDir_Min"])
            to_upload["WDir_Max"] = none_to_null(data[2]["WDir_Max"])
            to_upload["WDir_Avg"] = none_to_null(data[2]["WDir_Avg"])
            to_upload["WGst_Min"] = none_to_null(data[2]["WGst_Min"])
            to_upload["WGst_Max"] = none_to_null(data[2]["WGst_Max"])
            to_upload["WGst_Avg"] = none_to_null(data[2]["WGst_Avg"])
            to_upload["SunD_Ttl"] = none_to_null(data[2]["SunD_Ttl"])
            to_upload["Rain_Ttl"] = none_to_null(data[2]["Rain_Ttl"])
            to_upload["MSLP_Min"] = none_to_null(data[2]["MSLP_Min"])
            to_upload["MSLP_Max"] = none_to_null(data[2]["MSLP_Max"])
            to_upload["MSLP_Avg"] = none_to_null(data[2]["MSLP_Avg"])
            to_upload["ST10_Min"] = none_to_null(data[2]["ST10_Min"])
            to_upload["ST10_Max"] = none_to_null(data[2]["ST10_Max"])
            to_upload["ST10_Avg"] = none_to_null(data[2]["ST10_Avg"])
            to_upload["ST30_Min"] = none_to_null(data[2]["ST30_Min"])
            to_upload["ST30_Max"] = none_to_null(data[2]["ST30_Max"])
            to_upload["ST30_Avg"] = none_to_null(data[2]["ST30_Avg"])
            to_upload["ST00_Min"] = none_to_null(data[2]["ST00_Min"])
            to_upload["ST00_Max"] = none_to_null(data[2]["ST00_Max"])
            to_upload["ST00_Avg"] = none_to_null(data[2]["ST00_Avg"])

        # Upload the data
        try:
            request = requests.post(
                config.remote_sql_server, to_upload, timeout = 8)
            if request.text != "0": data_queue.appendleft(data); break
        except: data_queue.appendleft(data); break

    is_processing_data = False

def do_process_camera_queue():
    global camera_queue, is_processing_camera
    if is_processing_camera == True: return
    else: is_processing_camera = True

    # Process while there are items in the queue
    while len(camera_queue) > 0:
        data = camera_queue.popleft()
        if not os.path.isfile(data): continue

        try:
            ftp = ftplib.FTP(config.remote_ftp_server,
                config.remote_ftp_username, config.remote_ftp_password,
                timeout = 45)
            ftp.set_pasv(False); ftp.cwd("data"); ftp.cwd("camera")

            # Create nested folders for image date if necessary
            image_date = os.path.basename(data).split("T")[0].split("-")
            if image_date[0] not in ftp.nlst(): ftp.mkd(image_date[0])
            ftp.cwd(image_date[0])
            if image_date[1] not in ftp.nlst(): ftp.mkd(image_date[1])
            ftp.cwd(image_date[1])
            if image_date[2] not in ftp.nlst(): ftp.mkd(image_date[2])
            ftp.cwd(image_date[2])

            # Upload the image
            with open(data, "rb") as file:
                ftp.storbinary("STOR " + os.path.basename(data), file)
        except: camera_queue.appendleft(data); break

    is_processing_camera = False

# SCHEDULERS -------------------------------------------------------------------
def every_minute():
    utc = datetime.utcnow().replace(second = 0, microsecond = 0)
    local_time = helpers.utc_to_local(config, utc)

    # Get report data if config modifier is active
    if config.report_uploading == True:
        report = analysis.record_for_time(config, utc, DbTable.REPORTS)
    else: report == None

    # Get envReport data if config modifier is active
    if config.envReport_uploading == True:
        envReport = analysis.record_for_time(config, utc, DbTable.ENVREPORTS)
    else: envReport = None

    # Get dayStat data is config modifier is active
    if config.dayStat_uploading == True:
        dayStat = analysis.record_for_time(config, local_time, DbTable.DAYSTATS)
    else: dayStat = None

    # Add data to queue and process the queue
    data_queue.append((report, envReport, dayStat))
    do_process_data_queue()


    # Add camera image to queue if config modifier is active
    if config.camera_uploading == True:
        utc_minute = str(utc.minute)

        if utc_minute.endswith("0") or utc_minute.endswith("5"):
            image_path = os.path.join(config.camera_drive,
                utc.strftime("%Y/%m/%d/%Y-%m-%dT%H-%M-%S") + ".jpg")
            camera_queue.append(image_path)
            do_process_camera_queue()
    

# ENTRY POINT ==================================================================
def entry_point():
    global config; config.load()

    # -- START WATCHING DATA ---------------------------------------------------
    event_scheduler = BlockingScheduler()
    event_scheduler.add_job(every_minute, "cron", minute = "0-59", second = 8)
    event_scheduler.start()

if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.realpath(__file__))
    with daemon.DaemonContext(working_directory = current_dir):
        entry_point()