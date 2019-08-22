from datetime import datetime
import os
import urllib.request
from urllib.request import Request
import ftplib
import time
import sys

import daemon
from apscheduler.schedulers.blocking import BlockingScheduler
import RPi.GPIO as gpio

import routines.config as config
import routines.helpers as helpers
import routines.data as data


power_pressed = False
is_processing = False


def operation_shutdown(channel):
    """ Performs a system shutdown on press of the shutdown push button
    """
    global power_pressed
    if power_pressed == False:
        power_pressed = True
    else: return
    
    # Wait for safe time window to prevent data and upload corruption
    second = datetime.utcnow().second

    while second < 40 or second > 55:
        time.sleep(1)
        second = datetime.utcnow().second

    try:
        os.system("shutdown -h now")
    except: helpers.support_error("operation_shutdown() 0")

def operation_restart(channel):
    """ Performs a system restart on press of the restart push button
    """
    global power_pressed
    if power_pressed == False:
        power_pressed = True
    else: return

    # Wait for safe time window to prevent data and upload corruption
    second = datetime.utcnow().second

    while second < 40 or second > 55:
        time.sleep(1)
        second = datetime.utcnow().second

    try:
        os.system("shutdown -r now")
    except: helpers.support_error("operation_restart() 0")


def post_request(data):
    """ POSTs the specified data to the remote SQL database endpoint
    """
    try:
        request = Request(config.remote_sql_server,
            urllib.parse.urlencode(data).encode("utf-8"))
        response = urllib.request.urlopen(request, timeout=10)

        if response.read().decode() != "0":
            raise Exception("Success exit code not received")
    except: return False
    return True

def upload_report(report):
    """ Uploads a report
    """
    post_data = {
        "has_report": 1, "has_envReport": 0, "has_dayStat": 0
    }

    post_data["report_Time"] = report["Time"]
    post_data["report_AirT"] = helpers.none_to_null(report["AirT"])
    post_data["report_ExpT"] = helpers.none_to_null(report["ExpT"])
    post_data["report_RelH"] = helpers.none_to_null(report["RelH"])
    post_data["report_DewP"] = helpers.none_to_null(report["DewP"])
    post_data["report_WSpd"] = helpers.none_to_null(report["WSpd"])
    post_data["report_WDir"] = helpers.none_to_null(report["WDir"])
    post_data["report_WGst"] = helpers.none_to_null(report["WGst"])
    post_data["report_SunD"] = helpers.none_to_null(report["SunD"])
    post_data["report_Rain"] = helpers.none_to_null(report["Rain"])
    post_data["report_StaP"] = helpers.none_to_null(report["StaP"])
    post_data["report_MSLP"] = helpers.none_to_null(report["MSLP"])
    post_data["report_ST10"] = helpers.none_to_null(report["ST10"])
    post_data["report_ST30"] = helpers.none_to_null(report["ST30"])
    post_data["report_ST00"] = helpers.none_to_null(report["ST00"])

    return True if post_request(post_data) == True else False

def upload_envReport(envReport):
    """ Uploads an envReport
    """
    post_data = {
        "has_report": 0, "has_envReport": 1, "has_dayStat": 0
    }

    post_data["envReport_Time"] = envReport["Time"]
    post_data["envReport_EncT"] = helpers.none_to_null(envReport["EncT"])
    post_data["envReport_CPUT"] = helpers.none_to_null(envReport["CPUT"])

    return True if post_request(post_data) == True else False

def upload_dayStat(dayStat):
    """ Uploads a dayStat
    """
    post_data = {
        "has_report": 0, "has_envReport": 0, "has_dayStat": 1
    }

    post_data["dayStat_Date"] = dayStat["Date"]
    post_data["dayStat_AirT_Min"] = helpers.none_to_null(dayStat["AirT_Min"])
    post_data["dayStat_AirT_Max"] = helpers.none_to_null(dayStat["AirT_Max"])
    post_data["dayStat_AirT_Avg"] = helpers.none_to_null(dayStat["AirT_Avg"])
    post_data["dayStat_RelH_Min"] = helpers.none_to_null(dayStat["RelH_Min"])
    post_data["dayStat_RelH_Max"] = helpers.none_to_null(dayStat["RelH_Max"])
    post_data["dayStat_RelH_Avg"] = helpers.none_to_null(dayStat["RelH_Avg"])
    post_data["dayStat_DewP_Min"] = helpers.none_to_null(dayStat["DewP_Min"])
    post_data["dayStat_DewP_Max"] = helpers.none_to_null(dayStat["DewP_Max"])
    post_data["dayStat_DewP_Avg"] = helpers.none_to_null(dayStat["DewP_Avg"])
    post_data["dayStat_WSpd_Min"] = helpers.none_to_null(dayStat["WSpd_Min"])
    post_data["dayStat_WSpd_Max"] = helpers.none_to_null(dayStat["WSpd_Max"])
    post_data["dayStat_WSpd_Avg"] = helpers.none_to_null(dayStat["WSpd_Avg"])
    post_data["dayStat_WDir_Min"] = helpers.none_to_null(dayStat["WDir_Min"])
    post_data["dayStat_WDir_Max"] = helpers.none_to_null(dayStat["WDir_Max"])
    post_data["dayStat_WDir_Avg"] = helpers.none_to_null(dayStat["WDir_Avg"])
    post_data["dayStat_WGst_Min"] = helpers.none_to_null(dayStat["WGst_Min"])
    post_data["dayStat_WGst_Max"] = helpers.none_to_null(dayStat["WGst_Max"])
    post_data["dayStat_WGst_Avg"] = helpers.none_to_null(dayStat["WGst_Avg"])
    post_data["dayStat_SunD_Ttl"] = helpers.none_to_null(dayStat["SunD_Ttl"])
    post_data["dayStat_Rain_Ttl"] = helpers.none_to_null(dayStat["Rain_Ttl"])
    post_data["dayStat_MSLP_Min"] = helpers.none_to_null(dayStat["MSLP_Min"])
    post_data["dayStat_MSLP_Max"] = helpers.none_to_null(dayStat["MSLP_Max"])
    post_data["dayStat_MSLP_Avg"] = helpers.none_to_null(dayStat["MSLP_Avg"])
    post_data["dayStat_ST10_Min"] = helpers.none_to_null(dayStat["ST10_Min"])
    post_data["dayStat_ST10_Max"] = helpers.none_to_null(dayStat["ST10_Max"])
    post_data["dayStat_ST10_Avg"] = helpers.none_to_null(dayStat["ST10_Avg"])
    post_data["dayStat_ST30_Min"] = helpers.none_to_null(dayStat["ST30_Min"])
    post_data["dayStat_ST30_Max"] = helpers.none_to_null(dayStat["ST30_Max"])
    post_data["dayStat_ST30_Avg"] = helpers.none_to_null(dayStat["ST30_Avg"])
    post_data["dayStat_ST00_Min"] = helpers.none_to_null(dayStat["ST00_Min"])
    post_data["dayStat_ST00_Max"] = helpers.none_to_null(dayStat["ST00_Max"])
    post_data["dayStat_ST00_Avg"] = helpers.none_to_null(dayStat["ST00_Avg"])

    return True if post_request(post_data) == True else False

def upload_camReport(camReport):
    """ Uploads a camera image
    """
    image_path = os.path.join(config.camera_directory,
        camReport["Time"].strftime("%Y/%m/%d/%Y-%m-%dT%H-%M-%S") + ".jpg")

    if (os.path.isdir(config.camera_directory) and
        os.path.ismount(config.camera_directory) and
        os.path.isfile(image_path)):

        try:
            ftp = ftplib.FTP(config.remote_ftp_server,
                config.remote_ftp_username, config.remote_ftp_password,
                timeout=45)
            ftp.set_pasv(False)

            # Create y/m/d directory if doesn't exist already
            image_date = os.path.basename(image_path).split("T")[0].split("-")
            if image_date[0] not in ftp.nlst(): ftp.mkd(image_date[0])
            ftp.cwd(image_date[0])
            if image_date[1] not in ftp.nlst(): ftp.mkd(image_date[1])
            ftp.cwd(image_date[1])
            if image_date[2] not in ftp.nlst(): ftp.mkd(image_date[2])
            ftp.cwd(image_date[2])

            # Upload the image
            with open(image_path, "rb") as file:
                ftp.storbinary("STOR " + os.path.basename(image_path), file)
            return True

        except: return False
    else: return False


def schedule_minute():
    """ Triggered every minute to begin uploading of any non-uploaded data
    """
    global is_processing
    if is_processing: return
    is_processing = True

    # Retrieve each set of records from upload database
    reports = []
    if config.report_uploading == True:
        reportsQuery = data.query_database(
            config.upload_db_path, "SELECT * FROM reports LIMIT 200", None)

        if reportsQuery == False:
            helpers.support_error("schedule_minute() 0")
        elif reportsQuery != None: reports = reportsQuery

    envReports = []
    if config.envReport_uploading == True:
        envReportsQuery = data.query_database(
            config.upload_db_path, "SELECT * FROM envReports LIMIT 200", None)

        if envReportsQuery == False:
            helpers.support_error("schedule_minute() 1")
        elif envReportsQuery != None: envReports = envReportsQuery

    dayStats = []
    if config.dayStat_uploading == True:
        dayStatsQuery = data.query_database(
            config.upload_db_path, "SELECT * FROM dayStats LIMIT 200", None)

        if dayStatsQuery == False:
            helpers.support_error("schedule_minute() 2")
        elif dayStats != None: dayStats = dayStatsQuery

    camReports = []
    if config.camera_uploading == True:
        camReportsQuery = data.query_database(
            config.upload_db_path, "SELECT * FROM camReports LIMIT 200", None)

        if camReportsQuery == False: 
            helpers.support_error("schedule_minute() 3")
        elif camReports != None: camReports = camReportsQuery

    
    # Upload anything that was retrieved from the database
    while (len(reports) > 0 or len(envReports) > 0 or len(dayStats) > 0
        or len(camReports) > 0):

        if len(reports) > 0:
            if upload_report(reports[0]) == False:
                helpers.support_error("schedule_minute() 4")
                break
            
            else:
                query = data.query_database(config.upload_db_path,
                    "DELETE FROM reports WHERE Time = ?", (reports[0]["Time"],))
                if query == False: helpers.support_error("schedule_minute() 5")
                reports.pop(0)

        if len(envReports) > 0:
            if upload_envReport(envReports[0]) == False:
                helpers.support_error("schedule_minute() 6")
                break
            
            else:
                query = data.query_database(config.upload_db_path,
                    "DELETE FROM envReports WHERE Time = ?",
                    (envReports[0]["Time"],))
                if query == False: helpers.support_error("schedule_minute() 7")
                envReports.pop(0)

        if len(dayStats) > 0:
            if upload_dayStat(dayStats[0]) == False:
                helpers.support_error("schedule_minute() 8")
                break
            
            else:
                query = data.query_database(config.upload_db_path,
                    "DELETE FROM dayStats WHERE Date = ? AND Signature = ?",
                    (dayStats[0]["Date"], dayStats[0]["Signature"]))
                if query == False: helpers.support_error("schedule_minute() 9")
                dayStats.pop(0)

        if len(camReports) > 0:
            if upload_camReport(camReports[0]) == False:
                helpers.support_error("schedule_minute() 10")
                break
            
            else:
                query = data.query_database(config.upload_db_path,
                    "DELETE FROM camReports WHERE Time = ?",
                    (camReports[0]["Time"],))
                if query == False: helpers.support_error("schedule_minute() 11")
                camReports.pop(0)

    is_processing = False

def schedule_second():
    """ Triggered during a certain part of each minute to check for shutdown
        and restart commands
    """
    shutdown_cmd = os.path.join(config.data_directory, "shutdown.cmd")
    restart_cmd = os.path.join(config.data_directory, "restart.cmd")

    try:
        if os.path.isfile(shutdown_cmd):
            os.remove(shutdown_cmd)
            os.system("shutdown -h now")
        elif os.path.isfile(restart_cmd):
            os.remove(restart_cmd)
            os.system("shutdown -r now")
    except: helpers.support_error("schedule_second() 0")


if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.realpath(__file__))
    
    with daemon.DaemonContext(working_directory=current_dir):
        if config.load() == False: sys.exit(1)
        helpers.write_log("supp",
            "Support subsystem daemon started and loaded configuration")

        # Remove any temporary power command trigger files
        try:
            shutdown_cmd = os.path.join(config.data_directory, "shutdown.cmd")
            if os.path.isfile(shutdown_cmd): os.remove(shutdown_cmd)
            
            restart_cmd = os.path.join(config.data_directory, "restart.cmd")
            if os.path.isfile(restart_cmd): os.remove(restart_cmd)
        except: helpers.support_error("__main__() 0")

        # Set up power buttons
        gpio.setmode(gpio.BCM)

        if config.shutdown_pin != None:
            gpio.setup(config.shutdown_pin, gpio.IN, gpio.PUD_UP)
            gpio.add_event_detect(config.shutdown_pin, gpio.FALLING,
                callback=operation_shutdown, bouncetime=300)

        if config.restart_pin != None:
            gpio.setup(config.restart_pin, gpio.IN, gpio.PUD_UP)
            gpio.add_event_detect(config.restart_pin, gpio.FALLING,
                callback=operation_restart, bouncetime=300)

        # Start scheduler
        event_scheduler = BlockingScheduler()
        
        if (config.report_uploading == True or
            config.envReport_uploading == True or
            config.camera_uploading == True or
            config.dayStat_uploading == True):

            event_scheduler.add_job(schedule_minute, "cron", minute="0-59",
                second=6)

        event_scheduler.add_job(schedule_second, "cron", second="40-55")
        event_scheduler.start()