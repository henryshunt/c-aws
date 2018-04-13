""" CAWS Data Access Program
      Responsible for enabling access to and control of the station, and for
      serving its data to devices accessing from within the local network
"""

# DEPENDENCIES -----------------------------------------------------------------
import time
from datetime import datetime, timedelta
import os
import sys

import flask

import analysis
import helpers
from config import ConfigData
from frames import DbTable

# MESSAGE ----------------------------------------------------------------------
print("--- Custom Automatic Weather Station ---")
print("Program: Data Access Software")
print("Author:  Henry Hunt")
print("Version: V4.0 (April 2018)")
print("")
print("----------- DO NOT TERMINATE -----------")

# GLOBAL VARIABLES -------------------------------------------------------------
config = None
start_time = None

# PAGE SERVERS -----------------------------------------------------------------
def page_now():
    AirT = "no data"; ExpT = "no data"; RelH = "no data"; DewP = "no data"
    WSpd = "no data"; WDir = "no data"; WGst = "no data"; SunD = "no data"
    SunD_Phr = "no data"; Rain = "no data"; Rain_Phr = "no data"
    StaP = "no data"; MSLP = "no data"; PTen = "no data"; ST10 = "no data"
    ST30 = "no data"; ST00 = "no data"

    utc = datetime.utcnow().replace(second = 0, microsecond = 0)
    record = analysis.record_for_time(config, utc, DbTable.UTCREPORTS)

    # Try previous minute if no record for current minute
    if record == False or record == None:
        utc -= timedelta(minutes = 1)
        record = analysis.record_for_time(config, utc, DbTable.UTCREPORTS)

        # Return to current minute if no record for previous minute
        if record == False or record == None:
              utc += timedelta(minutes = 1)
            
    data_time = helpers.utc_to_local(config, utc).strftime("%H:%M")

    # Get values to display for each report parameter
    if record != False and record != None:
        if record["AirT"] != None:
            AirT = "{0:g}".format(record["AirT"]) + "°C"
        if record["ExpT"] != None:
            ExpT = "{0:g}".format(record["ExpT"]) + "°C"
        if record["RelH"] != None:
            RelH = "{0:g}".format(record["RelH"]) + "%"
        if record["DewP"] != None:
            DewP = "{0:g}".format(record["DewP"]) + "°C"
        if record["WSpd"] != None:
            WSpd = "{0:g}".format(record["WSpd"]) + " mph"
        
        if record["wdir"] != None:
            wdir_compass = helpers.degrees_to_compass(record["WDir"])
            WDir = str(record["WDir"]) + "° (" + wdir_compass + ")"
            
        if record["WGst"] != None:
            WGst = "{0:g}".format(record["WGst"]) + " mph"
        if record["SunD"] != None: SunD = str(record["SunD"]) + " sec"
        if record["Rain"] != None:
            Rain = "{0:g}".format(round(record["Rain"], 2)) + " mm"
        if record["StaP"] != None:
            StaP = "{0:g}".format(record["StaP"]) + " hPa"
        if record["MSLP"] != None:
            MSLP = "{0:g}".format(record["MSLP"]) + " hPa"

        if record["PTen"] != None:
            pten_phrase = helpers.tendency_to_phrase(record["PTen"])
            
            PTen = "+" if record["PTen"] > 0 else ""
            PTen += "{0:g}".format(record["PTen"]) + pten_phrase + " hPa"

        if record["ST10"] != None:
            ST10 = "{0:g}".format(record["ST10"]) + "°C"
        if record["ST30"] != None:
            ST30 = "{0:g}".format(record["ST30"]) + "°C"
        if record["ST00"] != None:
            ST00 = "{0:g}".format(record["ST00"]) + "°C"

    # Calculate total sunshine duration over past hour
    sund_phr_record = analysis.past_hour_total(config, utc, "SunD")

    if sund_phr_record != False and sund_phr_record != None:
        SunD_Phr = str(sund_phr_record["SunD"]) + " sec"

    # Calculate total rainfall over past hour
    rain_phr_record = analysis.past_hour_total(config, utc, "Rain")

    if rain_phr_record != False and rain_phr_record != None:
        Rain_Phr = "{0:g}".format(round(rain_phr_record["Rain"], 2)) + " mm"

    return flask.render_template("index.html",
                                 caws_name = config.caws_name,
                                 caws_location = config.caws_location,
                                 AirT = AirT, ExpT = ExpT, RelH = RelH,
                                 DewP = DewP, WSpd = WSpd, WDir = WDir,
                                 WGst = WGst, SunD = SunD, Rain = Rain,
                                 StaP = StaP, MSLP = MSLP, PTen = PTen,
                                 ST10 = ST10, ST30 = ST30, ST00 = ST00,
                                 SunD_Phr = SunD_Phr, Rain_Phr = Rain_Phr,
                                 data_time = data_time)

def page_statistics():
    AirT_Min = "no data"; AirT_Max = "no data"; AirT_Avg = "no data"
    RelH_Min = "no data"; RelH_Max = "no data"; RelH_Avg = "no data"
    DewP_Min = "no data"; DewP_Max = "no data"; DewP_Avg = "no data"
    WSpd_Min = "no data"; WSpd_Max = "no data"; WSpd_Avg = "no data"
    WDir_Min = "no data"; WDir_Max = "no data"; WDir_Avg = "no data"
    WGst_Min = "no data"; WGst_Max = "no data"; WGst_Avg = "no data"
    SunD_Ttl = "no data"; Rain_Ttl = "no data"; MSLP_Min = "no data"
    MSLP_Max = "no data"; MSLP_Avg = "no data"; ST10_Min = "no data"
    ST10_Max = "no data"; ST10_Avg = "no data"; ST30_Min = "no data"
    ST30_Max = "no data"; ST30_Avg = "no data"; ST00_Min = "no data"
    ST00_Max = "no data"; ST00_Avg = "no data"

    utc = datetime.utcnow().replace(second = 0, microsecond = 0)
    load_now_data = True

    # Check for local date specified in URL and try parsing
    if flask.request.args.get("date") != None:
        try:
            local_time = datetime.strptime(
                flask.request.args.get("date"), "%Y-%m-%d")
            
            # Remove date parameter if same as current date
            if (local_time.strftime("%Y-%m-%d")
                == helpers.utc_to_local(config, utc).strftime("%Y-%m-%d")):
                    return flask.redirect(flask.url_for("page_statistics"))

            load_now_data = False
        except: return flask.redirect(flask.url_for("page_statistics"))

    # Convert UTC to local if loading now data
    if load_now_data == True:
        local_time = helpers.utc_to_local(config, utc)
    
    record = analysis.record_for_time(config, local_time, DbTable.LOCALSTATS)

    # If loading now data, try previous minute if no record for current minute
    if record == False or record == None:
        if load_now_data == True:
            local_time -= timedelta(minutes = 1)
            record = analysis.record_for_time(config,
                                              local_time, DbTable.LOCALSTATS)

            # Return to current minute if no record for previous minute
            if record == False or record == None:
                  local_time += timedelta(minutes = 1)

    scroller_prev = (local_time - timedelta(days = 1)).strftime("%Y-%m-%d")
    scroller_time = local_time.strftime("%d/%m/%Y")
    scroller_next = (local_time + timedelta(days = 1)).strftime("%Y-%m-%d")
    data_time = helpers.utc_to_local(config, utc).strftime("%H:%M")

    # Get values to display for each report parameter
    if record != False and record != None:
        if record["AirT_Min"] != None:
            AirT_Min = "{0:g}".format(record["AirT_Min"]) + "°C"
        if record["AirT_Max"] != None:
            AirT_Max = "{0:g}".format(record["AirT_Max"]) + "°C"
        if record["AirT_Avg"] != None:
            AirT_Avg = "{0:g}".format(record["AirT_Avg"]) + "°C"
        if record["RelH_Min"] != None:
            RelH_Min = "{0:g}".format(record["RelH_Min"]) + "%"
        if record["RelH_Max"] != None:
            RelH_Max = "{0:g}".format(record["RelH_Max"]) + "%"
        if record["RelH_Avg"] != None:
            RelH_Avg = "{0:g}".format(record["RelH_Avg"]) + "%"
        if record["DewP_Min"] != None:
            DewP_Min = "{0:g}".format(record["DewP_Min"]) + "°C"
        if record["DewP_Max"] != None:
            DewP_Max = "{0:g}".format(record["DewP_Max"]) + "°C"
        if record["DewP_Avg"] != None:
            DewP_Avg = "{0:g}".format(record["DewP_Avg"]) + "°C"
        if record["WSpd_Min"] != None:
            WSpd_Min = "{0:g}".format(record["WSpd_Min"]) + " mph"
        if record["WSpd_Max"] != None:
            WSpd_Max = "{0:g}".format(record["WSpd_Max"]) + " mph"
        if record["WSpd_Avg"] != None:
            WSpd_Avg = "{0:g}".format(record["WSpd_Avg"]) + " mph"
        if record["WDir_Min"] != None:
            WDir_Min = str(record["WDir_Min"]) + "°"
        if record["WDir_Max"] != None:
            WDir_Max = str(record["WDir_Max"]) + "°"
        if record["WDir_Avg"] != None:
            WDir_Avg = str(record["WDir_Avg"]) + "°"
        if record["WGst_Min"] != None:
            WGst_Min = "{0:g}".format(record["WGst_Min"]) + " mph"
        if record["WGst_Max"] != None:
            WGst_Max = "{0:g}".format(record["WGst_Max"]) + " mph"
        if record["WGst_Avg"] != None:
            WGst_Avg = "{0:g}".format(record["WGst_Avg"]) + " mph"
        if record["SunD_Ttl"] != None:
            SunD_Ttl = str(record["SunD_Ttl"]) + " sec"
        if record["Rain_Ttl"] != None:
            Rain_Ttl = "{0:g}".format(round(record["Rain_Ttl"], 2)) + " mm"
        if record["MSLP_Min"] != None:
            MSLP_Min = "{0:g}".format(record["MSLP_Min"]) + " hPa"
        if record["MSLP_Max"] != None:
            MSLP_Max = "{0:g}".format(record["MSLP_Max"]) + " hPa"
        if record["MSLP_Avg"] != None:
            MSLP_Avg = "{0:g}".format(record["MSLP_Avg"]) + " hPa"
        if record["ST10_Min"] != None:
            ST10_Min = "{0:g}".format(record["ST10_Min"]) + "°C"
        if record["ST10_Max"] != None:
            ST10_Max = "{0:g}".format(record["ST10_Max"]) + "°C"
        if record["ST10_Avg"] != None:
            ST10_Avg = "{0:g}".format(record["ST10_Avg"]) + "°C"
        if record["ST30_Min"] != None:
            ST30_Min = "{0:g}".format(record["ST30_Min"]) + "°C"
        if record["ST30_Max"] != None:
            ST30_Max = "{0:g}".format(record["ST30_Max"]) + "°C"
        if record["ST30_Avg"] != None:
            ST30_Avg = "{0:g}".format(record["ST30_Avg"]) + "°C"
        
    return flask.render_template("statistics.html",
                                 caws_name = config.caws_name,
                                 caws_location = config.caws_location,
                                 scroller_prev = scroller_prev,
                                 scroller_time = scroller_time,
                                 scroller_next = scroller_next,
                                 AirT_Min = AirT_Min, AirT_Max = AirT_Max,
                                 AirT_Avg = AirT_Avg, RelH_Min = RelH_Min,
                                 RelH_Max = RelH_Max, RelH_Avg = RelH_Avg,
                                 DewP_Min = DewP_Min, DewP_Max = DewP_Max,
                                 DewP_Avg = DewP_Avg, WSpd_Min = WSpd_Min,
                                 WSpd_Max = WSpd_Max, WSpd_Avg = WSpd_Avg,
                                 WDir_Min = WDir_Min, WDir_Max = WDir_Max,
                                 WDir_Avg = WDir_Avg, WGst_Min = WGst_Min,
                                 WGst_Max = WGst_Max, WGst_Avg = WGst_Avg,
                                 SunD_Ttl = SunD_Ttl, Rain_Ttl = Rain_Ttl,
                                 MSLP_Min = MSLP_Min, MSLP_Max = MSLP_Max,
                                 MSLP_Avg = MSLP_Avg, ST10_Min = ST10_Min,
                                 ST10_Max = ST10_Max, ST10_Avg = ST10_Avg,
                                 ST30_Min = ST30_Min, ST30_Max = ST30_Max,
                                 ST30_Avg = ST30_Avg, ST00_Min = ST00_Min,
                                 ST00_Max = ST00_Max, ST00_Avg = ST00_Avg,
                                 data_time = data_time)

def page_graph_day():
    return "Graph Day"

def page_graph_month():
    return "Graph Month"

def page_graph_year():
    return "Graph Year"

def page_camera():
    utc = datetime.utcnow().replace(second = 0, microsecond = 0)
    load_now_data = True

    # Check for local time specified in URL and try parsing
    if flask.request.args.get("time") != None:
        try:
            local_time = datetime.strptime(
                flask.request.args.get("time"), "%Y-%m-%dT%H-%M")
            last_five = helpers.utc_to_local(config,
                                             helpers.last_five_mins(utc))

            # Remove time parameter if same as current time
            if (local_time.strftime("%Y-%m-%dT%H-%M")
                == last_five.strftime("%Y-%m-%dT%H-%M")):
                    return flask.redirect(flask.url_for("page_camera"))
                
            load_now_data = False
        except: return flask.redirect(flask.url_for("page_camera"))

    # Convert UTC to local if loading now data
    if load_now_data == True:
        local_time = helpers.utc_to_local(config, helpers.last_five_mins(utc))

        # Try previous 5 mins if no image for current 5 min
        to_utc = helpers.local_to_utc(config, local_time)
        image_dir = os.path.join(config.camera_drive,
                                 to_utc.strftime("%Y/%m/%d"))
        image_name = to_utc.strftime("%Y-%m-%dT%H-%M-%S.jpg")
                
        if not os.path.isfile(os.path.join(image_dir, image_name)):
            local_time -= timedelta(minutes = 5)
            to_utc = helpers.local_to_utc(config, local_time)
            image_dir = os.path.join(config.camera_drive,
                                     to_utc.strftime("%Y/%m/%d"))
            image_name = to_utc.strftime("%Y-%m-%dT%H-%M-%S.jpg")

            # Return to current 5 mins if no image for previous 5 mins
            if not os.path.isfile(os.path.join(image_dir, image_name)):
                local_time += timedelta(minutes = 5)

    delta = timedelta(minutes = 5)
    scroller_prev = (local_time - delta).strftime("%Y-%m-%dT%H-%M")
    scroller_time = local_time.strftime("%d/%m/%Y %H:%M")
    scroller_next = (local_time + delta).strftime("%Y-%m-%dT%H-%M")
    image_path = "camera/" + local_time.strftime("%Y-%m-%dT%H-%M-%S.jpg")
    data_time = local_time.strftime("%H:%M")

    return flask.render_template("camera.html",
                                 caws_name = config.caws_name,
                                 caws_location = config.caws_location,
                                 scroller_prev = scroller_prev,
                                 scroller_time = scroller_time,
                                 scroller_next = scroller_next,
                                 image_path = image_path,
                                 data_time = data_time)

def page_about():
    return "About"

def file_camera(file_name):
    try:
        local_time = datetime.strptime(file_name, "%Y-%m-%dT%H-%M-%S.jpg")
        utc = helpers.local_to_utc(config, local_time)

        # Generate path to local image from supplied URL
        image_dir = os.path.join(config.camera_drive, utc.strftime("%Y/%m/%d"))
        image_name = utc.strftime("%Y-%m-%dT%H-%M-%S.jpg")

        # Return error image if file does not exist
        if not os.path.isfile(os.path.join(image_dir, image_name)):
           return flask.send_from_directory("server", "no_camera_image.png") 

        return flask.send_from_directory(image_dir, image_name)
    except: return flask.send_from_directory("server", "no_camera_image.png")


# ENTRY POINT ==================================================================
# -- LOAD CONFIG ---------------------------------------------------------------
config = ConfigData()
if config.load() == False: sys.exit(1)
if config.validate() == False: sys.exit(1)

# -- CREATE SERVER -------------------------------------------------------------
server = flask.Flask(__name__, static_folder = "server",
                     template_folder = "server")

# -- ROUTE URLS ----------------------------------------------------------------
server.add_url_rule("/", view_func = page_now)
server.add_url_rule("/index.html", view_func = page_now)
server.add_url_rule("/statistics.html", view_func = page_statistics)
server.add_url_rule("/graph_day.html", view_func = page_graph_day)
server.add_url_rule("/graph_month.html", view_func = page_graph_month)
server.add_url_rule("/graph_year.html", view_func = page_graph_year)
server.add_url_rule("/camera.html", view_func = page_camera)
server.add_url_rule("/about.html", view_func = page_about)
server.add_url_rule("/camera/<file_name>", view_func = file_camera)

# -- START SERVER --------------------------------------------------------------
start_time = datetime.utcnow().replace(second = 0, microsecond = 0)
server.run(host = "0.0.0.0", threaded = True)
