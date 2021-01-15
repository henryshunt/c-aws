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
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

import routines.config as config
import routines.helpers as helpers
import routines.data as data


is_uploading = False
power_command = None


def execute_power_command():
    """ Executes a system shutdown or restart based on the loaded command
    """
    global power_command

    try:
        os.system("shutdown -"
            + "h" if power_command == "shutdown" else "r" + " now")
    except: helpers.supp_error("execute_power_command() 0")
    power_command = None

class PCTFHandler(FileSystemEventHandler):
    """ Watches for creation and modification of a power command trigger file
        in the data directory
    """

    def on_modified(self, event):
        global power_command
        if event.is_directory == True or power_command != None: return

        if os.path.basename(event.src_path) == "power":
            try:
                with open(event.src_path, "r") as trigger_file:
                    trigger_val = trigger_file.read()
                    if trigger_val != "shutdown" and trigger_val != "restart":
                        return

                    power_command = trigger_val
                    if config.power_led_pin != None:
                        gpio.output(config.power_led_pin, gpio.HIGH)

                    second = datetime.utcnow().second
                    if second >= 30 and second <= 55: execute_power_command()
            except: helpers.supp_error("on_modified() 0")

def operation_shutdown(channel):
    """ Triggers a system shutdown on press of the shutdown button
    """
    trigger_path = os.path.join(config.data_directory, "power")
    with open(trigger_path, "w") as trigger_file:
        trigger_file.write("shutdown")

def operation_restart(channel):
    """ Triggers a system restart on press of the restart button
    """
    trigger_path = os.path.join(config.data_directory, "power")
    with open(trigger_path, "w") as trigger_file:
        trigger_file.write("restart") 


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

    try:
        if (os.path.isdir(config.camera_directory) and
            os.path.ismount(config.camera_directory) and
            os.path.isfile(image_path)):

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

        else: return False
    except: return False


def schedule_minute():
    """ Triggered every minute to begin uploading of any non-uploaded data
    """
    global is_uploading
    if is_uploading: return
    is_uploading = True

    # Retrieve each set of records from upload database
    reports = []
    if config.report_uploading == True:
        reportsQuery = data.query_database(
            config.upload_db_path, "SELECT * FROM reports LIMIT 200", None)

        if reportsQuery == False:
            helpers.supp_error("schedule_minute() 0")
        elif reportsQuery != None: reports = reportsQuery

    envReports = []
    if config.envReport_uploading == True:
        envReportsQuery = data.query_database(
            config.upload_db_path, "SELECT * FROM envReports LIMIT 200", None)

        if envReportsQuery == False:
            helpers.supp_error("schedule_minute() 1")
        elif envReportsQuery != None: envReports = envReportsQuery

    dayStats = []
    if config.dayStat_uploading == True:
        dayStatsQuery = data.query_database(
            config.upload_db_path, "SELECT * FROM dayStats LIMIT 200", None)

        if dayStatsQuery == False:
            helpers.supp_error("schedule_minute() 2")
        elif dayStats != None: dayStats = dayStatsQuery

    camReports = []
    if config.camera_uploading == True:
        camReportsQuery = data.query_database(
            config.upload_db_path, "SELECT * FROM camReports LIMIT 200", None)

        if camReportsQuery == False: 
            helpers.supp_error("schedule_minute() 3")
        elif camReports != None: camReports = camReportsQuery

    
    # Upload anything that was retrieved from the database
    while (len(reports) > 0 or len(envReports) > 0 or len(dayStats) > 0
        or len(camReports) > 0):

        if len(reports) > 0:
            if upload_report(reports[0]) == False:
                helpers.supp_error("schedule_minute() 4")
                break
            
            else:
                query = data.query_database(config.upload_db_path,
                    "DELETE FROM reports WHERE Time = ?", (reports[0]["Time"],))
                if query == False: helpers.supp_error("schedule_minute() 5")
                reports.pop(0)

        if len(envReports) > 0:
            if upload_envReport(envReports[0]) == False:
                helpers.supp_error("schedule_minute() 6")
                break
            
            else:
                query = data.query_database(config.upload_db_path,
                    "DELETE FROM envReports WHERE Time = ?",
                    (envReports[0]["Time"],))
                if query == False: helpers.supp_error("schedule_minute() 7")
                envReports.pop(0)

        if len(dayStats) > 0:
            if upload_dayStat(dayStats[0]) == False:
                helpers.supp_error("schedule_minute() 8")
                break
            
            else:
                query = data.query_database(config.upload_db_path,
                    "DELETE FROM dayStats WHERE Date = ? AND Signature = ?",
                    (dayStats[0]["Date"], dayStats[0]["Signature"]))
                if query == False: helpers.supp_error("schedule_minute() 9")
                dayStats.pop(0)

        if len(camReports) > 0:
            if upload_camReport(camReports[0]) == False:
                helpers.supp_error("schedule_minute() 10")
                break
            
            else:
                query = data.query_database(config.upload_db_path,
                    "DELETE FROM camReports WHERE Time = ?",
                    (camReports[0]["Time"],))
                if query == False: helpers.supp_error("schedule_minute() 11")
                camReports.pop(0)

    is_uploading = False

def schedule_power_command():
    """ Triggered once per minute to execute a power command if requested
    """
    if power_command != None: execute_power_command()


if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.realpath(__file__))
    
    with daemon.DaemonContext(working_directory=current_dir):
        if config.load() == False: sys.exit(1)
        helpers.write_log("supp",
            "Support subsystem daemon started and loaded configuration")

        # Set up and reset power command indicator LED
        gpio.setmode(gpio.BCM)
        if config.power_led_pin != None:
            gpio.setup(config.power_led_pin, gpio.OUT)
            gpio.output(config.power_led_pin, gpio.LOW)
        
        # Set up power command buttons
        if config.shutdown_pin != None:
            gpio.setup(config.shutdown_pin, gpio.IN, gpio.PUD_UP)
            gpio.add_event_detect(config.shutdown_pin, gpio.FALLING,
                callback=operation_shutdown, bouncetime=1000)
                
        if config.restart_pin != None:
            gpio.setup(config.restart_pin, gpio.IN, gpio.PUD_UP)
            gpio.add_event_detect(config.restart_pin, gpio.FALLING,
                callback=operation_restart, bouncetime=1000)

        # Remove power command trigger file
        trigger_path = os.path.join(config.data_directory, "power")

        try:
            if os.path.isfile(trigger_path): os.remove(trigger_path)
        except: helpers.supp_error("__main__() 0")


        # Start power command trigger file watcher
        power_command_watcher = Observer()
        power_command_watcher.schedule(
            PCTFHandler(), path=config.data_directory, recursive=False)
        power_command_watcher.start()

        # Start scheduler
        event_scheduler = BlockingScheduler()

        if (config.report_uploading == True or
            config.envReport_uploading == True or
            config.camera_uploading == True or
            config.dayStat_uploading == True):

            event_scheduler.add_job(schedule_minute, "cron", minute="0-59",
                second=6)

        event_scheduler.add_job(schedule_power_command, "cron", second="30")
        event_scheduler.start()