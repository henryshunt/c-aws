from datetime import datetime
import os
import threading
import urllib.request
from collections import deque
import ftplib
import time
import sys

import daemon
from apscheduler.schedulers.blocking import BlockingScheduler
import RPi.GPIO as gpio

import routines.config as config
import routines.helpers as helpers
from routines.frames import DbTable
import routines.analysis as analysis

power_pressed = False

data_queue = deque(maxlen = 10080)
is_processing_data = False
camera_queue = deque(maxlen = 2016)
is_processing_camera = False

def operation_process_data():
    """ Attempts to upload all elements in the data queue, aborting on failure
    """
    global is_processing_data, data_queue
    if is_processing_data == True: return
    else: is_processing_data = True

    # Process while there are items in the queue
    while data_queue:
        data = data_queue.popleft()

        to_upload = {
            "has_report": 0 if data[0] == False or data[0] == None else 1,
            "has_envReport": 0 if data[1] == False or data[1] == None else 1,
            "has_dayStat": 0 if data[2] == False or data[2] == None else 1
        }

        # Add report data to data to upload
        if to_upload["has_report"] == 1:
            to_upload["report_Time"] = data[0]["Time"]
            to_upload["report_AirT"] = helpers.none_to_null(data[0]["AirT"])
            to_upload["report_ExpT"] = helpers.none_to_null(data[0]["ExpT"])
            to_upload["report_RelH"] = helpers.none_to_null(data[0]["RelH"])
            to_upload["report_DewP"] = helpers.none_to_null(data[0]["DewP"])
            to_upload["report_WSpd"] = helpers.none_to_null(data[0]["WSpd"])
            to_upload["report_WDir"] = helpers.none_to_null(data[0]["WDir"])
            to_upload["report_WGst"] = helpers.none_to_null(data[0]["WGst"])
            to_upload["report_SunD"] = helpers.none_to_null(data[0]["SunD"])
            to_upload["report_Rain"] = helpers.none_to_null(data[0]["Rain"])
            to_upload["report_StaP"] = helpers.none_to_null(data[0]["StaP"])
            to_upload["report_MSLP"] = helpers.none_to_null(data[0]["MSLP"])
            to_upload["report_ST10"] = helpers.none_to_null(data[0]["ST10"])
            to_upload["report_ST30"] = helpers.none_to_null(data[0]["ST30"])
            to_upload["report_ST00"] = helpers.none_to_null(data[0]["ST00"])

        # Add envReport data to data to upload
        if to_upload["has_envReport"] == 1:
            to_upload["envReport_Time"] = data[1]["Time"]
            to_upload["envReport_EncT"] = helpers.none_to_null(data[1]["EncT"])
            to_upload["envReport_CPUT"] = helpers.none_to_null(data[1]["CPUT"])

        # Add dayStat data to data to upload
        if to_upload["has_dayStat"] == 1:
            to_upload["dayStat_Date"] = data[2]["Date"]
            to_upload["dayStat_AirT_Min"] = helpers.none_to_null(data[2][
                "AirT_Min"])
            to_upload["dayStat_AirT_Max"] = helpers.none_to_null(data[2][
                "AirT_Max"])
            to_upload["dayStat_AirT_Avg"] = helpers.none_to_null(data[2][
                "AirT_Avg"])
            to_upload["dayStat_RelH_Min"] = helpers.none_to_null(data[2][
                "RelH_Min"])
            to_upload["dayStat_RelH_Max"] = helpers.none_to_null(data[2][
                "RelH_Max"])
            to_upload["dayStat_RelH_Avg"] = helpers.none_to_null(data[2][
                "RelH_Avg"])
            to_upload["dayStat_DewP_Min"] = helpers.none_to_null(data[2][
                "DewP_Min"])
            to_upload["dayStat_DewP_Max"] = helpers.none_to_null(data[2][
                "DewP_Max"])
            to_upload["dayStat_DewP_Avg"] = helpers.none_to_null(data[2][
                "DewP_Avg"])
            to_upload["dayStat_WSpd_Min"] = helpers.none_to_null(data[2][
                "WSpd_Min"])
            to_upload["dayStat_WSpd_Max"] = helpers.none_to_null(data[2][
                "WSpd_Max"])
            to_upload["dayStat_WSpd_Avg"] = helpers.none_to_null(data[2][
                "WSpd_Avg"])
            to_upload["dayStat_WDir_Min"] = helpers.none_to_null(data[2][
                "WDir_Min"])
            to_upload["dayStat_WDir_Max"] = helpers.none_to_null(data[2][
                "WDir_Max"])
            to_upload["dayStat_WDir_Avg"] = helpers.none_to_null(data[2][
                "WDir_Avg"])
            to_upload["dayStat_WGst_Min"] = helpers.none_to_null(data[2][
                "WGst_Min"])
            to_upload["dayStat_WGst_Max"] = helpers.none_to_null(data[2][
                "WGst_Max"])
            to_upload["dayStat_WGst_Avg"] = helpers.none_to_null(data[2][
                "WGst_Avg"])
            to_upload["dayStat_SunD_Ttl"] = helpers.none_to_null(data[2][
                "SunD_Ttl"])
            to_upload["dayStat_Rain_Ttl"] = helpers.none_to_null(data[2][
                "Rain_Ttl"])
            to_upload["dayStat_MSLP_Min"] = helpers.none_to_null(data[2][
                "MSLP_Min"])
            to_upload["dayStat_MSLP_Max"] = helpers.none_to_null(data[2][
                "MSLP_Max"])
            to_upload["dayStat_MSLP_Avg"] = helpers.none_to_null(data[2][
                "MSLP_Avg"])
            to_upload["dayStat_ST10_Min"] = helpers.none_to_null(data[2][
                "ST10_Min"])
            to_upload["dayStat_ST10_Max"] = helpers.none_to_null(data[2][
                "ST10_Max"])
            to_upload["dayStat_ST10_Avg"] = helpers.none_to_null(data[2][
                "ST10_Avg"])
            to_upload["dayStat_ST30_Min"] = helpers.none_to_null(data[2][
                "ST30_Min"])
            to_upload["dayStat_ST30_Max"] = helpers.none_to_null(data[2][
                "ST30_Max"])
            to_upload["dayStat_ST30_Avg"] = helpers.none_to_null(data[2][
                "ST30_Avg"])
            to_upload["dayStat_ST00_Min"] = helpers.none_to_null(data[2][
                "ST00_Min"])
            to_upload["dayStat_ST00_Max"] = helpers.none_to_null(data[2][
                "ST00_Max"])
            to_upload["dayStat_ST00_Avg"] = helpers.none_to_null(data[2][
                "ST00_Avg"])

        # Upload the data        
        try:
            request = urllib.request.Request(config.remote_sql_server,
                urllib.parse.urlencode(to_upload).encode("utf-8"))
            response = urllib.request.urlopen(request, timeout = 10)
            if response.read().decode() != "0": raise Exception()

        except:
            data_queue.appendleft(data)
            helpers.data_error_blind(52)
            break

    is_processing_data = False

def operation_process_camera():
    """ Attempts to upload all elements in the camera queue, aborting on failure
    """
    global is_processing_camera, camera_queue
    if is_processing_camera == True: return
    else: is_processing_camera = True

    # Process while there are items in the queue
    while camera_queue:
        data = camera_queue.popleft()

        if (os.path.isdir(config.camera_directory) and
            os.path.ismount(config.camera_directory) and
            os.path.isfile(data)):

            try:
                ftp = ftplib.FTP(config.remote_ftp_server,
                    config.remote_ftp_username, config.remote_ftp_password,
                    timeout = 45)
                ftp.set_pasv(False)

                # Create y/m/d directory if doesn't exist already
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

            except:
                camera_queue.appendleft(data)
                helpers.data_error_blind(56)
                break

        else:
            helpers.data_error_blind(55)
            return

    is_processing_camera = False

def operation_shutdown(channel):
    """ Performs a system shutdown on press of the shutdown push button
    """
    global power_pressed
    if power_pressed == False: power_pressed = True
    else: return
    
    # Wait for safe time window to prevent data and upload corruption
    second = datetime.utcnow().second

    while second < 35 or second > 55:
        time.sleep(0.8)
        second = datetime.utcnow().second

    try:
        os.system("shutdown -h now")
    except: helpers.data_error_blind(57)

def operation_restart(channel):
    """ Performs a system restart on press of the restart push button
    """
    global power_pressed
    if power_pressed == False: power_pressed = True
    else: return

    # Wait for safe time window to prevent data and upload corruption
    second = datetime.utcnow().second

    while second < 35 or second > 55:
        time.sleep(0.8)
        second = datetime.utcnow().second

    try:
        os.system("shutdown -r now")
    except: helpers.data_error_blind(58)


def schedule_minute():
    """ Triggered every minute to add new data to the upload queues and to try
        and process the queues
    """
    global data_queue, camera_queue
    utc = datetime.utcnow().replace(second = 0, microsecond = 0)
    local_time = helpers.utc_to_local(utc)

    # Get database records depending on if uploading them is active
    if (config.report_uploading == True or config.envReport_uploading == True
        or config.dayStat_uploading == True):

        if config.report_uploading == True:
            report = analysis.record_for_time(utc, DbTable.REPORTS)
        else: report == None

        if config.envReport_uploading == True:
            envReport = analysis.record_for_time(utc, DbTable.ENVREPORTS)
        else: envReport = None

        if config.dayStat_uploading == True:
            dayStat = analysis.record_for_time(local_time, DbTable.DAYSTATS)
        else: dayStat = None

        if report == False or envReport == False or dayStat == False:
            helpers.data_error_blind(59)

        # Add data to queue and process the queue
        if ((report != False and report != None) or (envReport != False and
            envReport != None) or (dayStat != False and dayStat != None)):

            data_queue.append((report, envReport, dayStat))
        threading.Thread(target = operation_process_data).start()

    # Add camera image to queue if camera uploading is active
    if config.camera_uploading == True:
        utc_minute = str(utc.minute)

        if utc_minute.endswith("0") or utc_minute.endswith("5"):
            image_path = os.path.join(config.camera_directory,
                utc.strftime("%Y/%m/%d/%Y-%m-%dT%H-%M-%S") + ".jpg")

            if (os.path.isdir(config.camera_directory) and
                os.path.ismount(config.camera_directory) and
                os.path.isfile(image_path)):

                camera_queue.append(image_path)        
        threading.Thread(target = operation_process_camera).start()

def schedule_second():
    """ Triggered during a certain part of each minute to check for shutdown
        and restart commands
    """
    try:
        if os.path.isfile(os.path.join(config.data_directory, "shutdown.cmd")):
            os.remove(os.path.join(config.data_directory, "shutdown.cmd"))
            os.system("shutdown -h now")

        elif os.path.isfile(os.path.join(config.data_directory, "restart.cmd")):
            os.remove(os.path.join(config.data_directory, "restart.cmd"))
            os.system("shutdown -r now")
    except: helpers.data_error_blind(51)


if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.realpath(__file__))
    
    with daemon.DaemonContext(working_directory = current_dir):
        if config.load() == False: sys.exit()

        # REMOVE TEMP FILES ----------------------------------------------------
        try:
            path = os.path.join(config.data_directory, "shutdown.cmd")
            if os.path.isfile(path): os.remove(path)
            
            path = os.path.join(config.data_directory, "restart.cmd")
            if os.path.isfile(path): os.remove(path)
        except: sys.exit()

        # SETUP POWER BUTTONS --------------------------------------------------
        gpio.setwarnings(False)
        gpio.setmode(gpio.BCM)

        gpio.setup(17, gpio.IN, gpio.PUD_UP)
        gpio.add_event_detect(17, gpio.FALLING, callback = operation_shutdown,
                            bouncetime = 300)
        gpio.setup(18, gpio.IN, gpio.PUD_UP)
        gpio.add_event_detect(18, gpio.FALLING, callback = operation_restart,
                            bouncetime = 300)

        # -- START WATCHING DATA -----------------------------------------------
        event_scheduler = BlockingScheduler()
        
        if (config.report_uploading == True or
            config.envReport_uploading == True or
            config.dayStat_uploading == True or
            config.camera_uploading == True):

            event_scheduler.add_job(schedule_minute, "cron", minute = "0-59",
                second = 8)

        event_scheduler.add_job(schedule_second, "cron", second = "35-55")
        event_scheduler.start()