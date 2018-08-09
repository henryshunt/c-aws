""" C-AWS Data Access Program
      Responsible for enabling station control and local data viewing
"""

# DEPENDENCIES -----------------------------------------------------------------
import time
from datetime import datetime, timedelta
import os
import sys
import logging
import RPi.GPIO as gpio
import threading

import daemon
import flask
import astral

import analysis
import helpers
from config import ConfigData
from frames import DbTable

# GLOBAL VARIABLES -------------------------------------------------------------
config = ConfigData()
startup_time = None

# INTERRUPTS -------------------------------------------------------------------
def do_shutdown(channel):
    os.system("sudo halt")

def do_restart(channel):
    os.system("sudo reboot")

# PAGE SERVERS -----------------------------------------------------------------
def page_now():
    global config

    return flask.render_template("index.html",
                                 aws_title = config.aws_location.split(",")[0],
                                 aws_location = config.aws_location,
                                 aws_time_zone = config.aws_time_zone)

def page_statistics():
    global config

    return flask.render_template("statistics.html",
                                 aws_title = config.aws_location.split(",")[0],
                                 aws_location = config.aws_location,
                                 aws_time_zone = config.aws_time_zone)

def page_graph_day():
    global config

    return flask.render_template("graph-day.html",
                                 aws_title = config.aws_location.split(",")[0],
                                 aws_location = config.aws_location,
                                 aws_time_zone = config.aws_time_zone)

def page_graph_month():
    global config

    return flask.render_template("graph-month.html",
                                 aws_title = config.aws_location.split(",")[0],
                                 aws_location = config.aws_location,
                                 aws_time_zone = config.aws_time_zone)

def page_graph_year():
    global config

    return flask.render_template("graph-year.html",
                                 aws_title = config.aws_location.split(",")[0],
                                 aws_location = config.aws_location,
                                 aws_time_zone = config.aws_time_zone)

def page_camera():
    global config

    return flask.render_template("camera.html",
                                 aws_title = config.aws_location.split(",")[0],
                                 aws_location = config.aws_location,
                                 aws_time_zone = config.aws_time_zone)

def page_about():
    global config

    return flask.render_template("about.html",
                                 aws_title = config.aws_location.split(",")[0],
                                 aws_location = config.aws_location,
                                 aws_time_zone = config.aws_time_zone,
                                 aws_elevation = config.aws_elevation,
                                 aws_latitude = config.aws_latitude,
                                 aws_longitude = config.aws_longitude)

# DATA PAGE SERVERS ------------------------------------------------------------
def data_now():
    global config
    data = dict.fromkeys(["Time", "AirT", "ExpT", "RelH", "DewP", "WSpd",
                          "WDir", "WGst", "SunD", "SunD_PHr", "Rain",
                          "Rain_PHr", "StaP", "MSLP", "StaP_PTH", "ST10",
                          "ST30", "ST00"])

    # Try parsing time specified in URL
    if flask.request.args.get("time") == None: return flask.jsonify(data)
    try:
        url_time = datetime.strptime(
            flask.request.args.get("time"), "%Y-%m-%dT%H-%M-%S")
    except: return flask.jsonify(data)

    # Get record for that time
    record = analysis.record_for_time(config, url_time, DbTable.REPORTS)

    if record != False:
        if record == None:
            # Go back a minute if no record and not in absolute mode
            if not flask.request.args.get("abs") == "1":
                url_time -= timedelta(minutes = 1)
                record = analysis.record_for_time(config, url_time,
                                                  DbTable.REPORTS)
                
                if record != False:
                    if record != None:
                        # Add record data to final data
                        for key in dict(zip(record.keys(), record)):
                            if key in data: data[key] = record[key]
                    else: url_time += timedelta(minutes = 1)
                else: url_time += timedelta(minutes = 1)
                    
        else:
            # Add record data to final data
            for key in dict(zip(record.keys(), record)):
                if key in data: data[key] = record[key]

    # Calculate total sunshine duration over past hour
    SunD_PHr_record = analysis.past_hour_total(config, url_time, "SunD")
    if SunD_PHr_record != False and SunD_PHr_record != None:
        data["SunD_PHr"] = SunD_PHr_record["SunD_PHr"]

    # Calculate total rainfall over past hour
    Rain_PHr_record = analysis.past_hour_total(config, url_time, "Rain")
    if Rain_PHr_record != False and Rain_PHr_record != None:
        data["Rain_PHr"] = Rain_PHr_record["Rain_PHr"]

    # Calculate three hour pressure tendency
    if data["StaP"] != None:
        StaP_PTH_record = analysis.record_for_time(config,
            url_time - timedelta(hours = 3), DbTable.REPORTS)
    
        if StaP_PTH_record != False and StaP_PTH_record != None:
            if StaP_PTH_record["StaP"] != None:
                data["StaP_PTH"] = data["StaP"] - StaP_PTH_record["StaP"]

    data["Time"] = url_time.strftime("%Y-%m-%d %H:%M:%S")
    return flask.jsonify(data)

def data_statistics():
    global config
    data = dict.fromkeys(["Time", "AirT_Min", "AirT_Max", "AirT_Avg",
                          "RelH_Min", "RelH_Max", "RelH_Avg", "DewP_Min",
                          "DewP_Max", "DewP_Avg", "WSpd_Min", "WSpd_Max",
                          "WSpd_Avg", "WDir_Min", "WDir_Max", "WDir_Avg",
                          "WGst_Min", "WGst_Max", "WGst_Avg", "SunD_Ttl",
                          "Rain_Ttl", "MSLP_Min", "MSLP_Max", "MSLP_Avg",
                          "ST10_Min", "ST10_Max", "ST10_Avg", "ST30_Min",
                          "ST30_Max", "ST30_Avg", "ST00_Min", "ST00_Max",
                          "ST00_Avg"])

    # Try parsing time specified in URL
    if flask.request.args.get("time") == None: return flask.jsonify(data)
    try:
        url_time = datetime.strptime(
            flask.request.args.get("time"), "%Y-%m-%dT%H-%M-%S")
        local_time = helpers.utc_to_local(config, url_time)
    except: return flask.jsonify(data)

    # Get record for that time
    record = analysis.record_for_time(config, local_time, DbTable.DAYSTATS)

    if record != False:
        if record == None:
            # Go back a minute if no record and not in absolute mode
            if not flask.request.args.get("abs") == "1":
                url_time -= timedelta(minutes = 1)
                record = analysis.record_for_time(config, url_time,
                                                  DbTable.DAYSTATS)
                
                if record != False:
                    if record != None:
                        # Add record data to final data
                        for key in dict(zip(record.keys(), record)):
                            if key in data: data[key] = record[key]
                    else: url_time += timedelta(minutes = 1)
                else: url_time += timedelta(minutes = 1)
                    
        else:
            # Add record data to final data
            for key in dict(zip(record.keys(), record)):
                if key in data: data[key] = record[key]

    data["Time"] = url_time.strftime("%Y-%m-%d %H:%M:%S")
    return flask.jsonify(data)

def data_graph_day():
    global config; data = []
    if flask.request.args.get("time") == None: return flask.jsonify(data)
    try:
        url_time = datetime.strptime(
            flask.request.args.get("time"), "%Y-%m-%dT%H-%M-%S")
    except: return flask.jsonify(data)

    bounds = helpers.day_bounds_utc(
        config, helpers.utc_to_local(config, url_time), True)
    fields = "Time," + flask.request.args.get("fields")

    # Get data in range for specified parameters
    records = analysis.fields_in_range(config, bounds[0], bounds[1], fields,
        DbTable.REPORTS)

    if records == False or len(records) == 0: return flask.jsonify(data)
    fields = fields.split(",")
    for field in range(1, len(fields)): data.append([])

    if "Rain" in fields: Rain_Ttl = 0
    if "SunD" in fields: SunD_Ttl = 0

    # Generate each series from retrieved records 
    for record in records:
        utc = datetime.strptime(record["Time"], "%Y-%m-%d %H:%M:%S").timestamp()

        # Create point and add to relevant series
        for field in range(1, len(fields)):
            if fields[field] == "Rain":
                if record[fields[field]] != None:
                    Rain_Ttl += record[fields[field]]
                point = { "x": utc, "y": round(Rain_Ttl, 2) }

            elif fields[field] == "SunD":
                if record[fields[field]] != None:
                    SunD_Ttl += record[fields[field]]
                point = { "x": utc, "y": round(SunD_Ttl, 2) }
            else: point = { "x": utc, "y": record[fields[field]] }

            data[field - 1].append(point)
    return flask.jsonify(data)

def data_graph_year():
    global config; data = []
    if flask.request.args.get("time") == None: return flask.jsonify(data)
    try:
        url_time = datetime.strptime(
            flask.request.args.get("time"), "%Y-%m-%dT%H-%M-%S")
    except: return flask.jsonify(data)

    bounds = helpers.day_bounds_utc(
        config, helpers.utc_to_local(config, url_time), True)
    range_end = bounds[0] - timedelta(minutes = 1)
    range_start = range_end - timedelta(days = 365)
    fields = "Date," + flask.request.args.get("fields")

    # Get data in range for specified parameters
    records = analysis.fields_in_range(config, range_start, range_end, fields,
        DbTable.DAYSTATS)

    if records == False or len(records) == 0: return flask.jsonify(data)
    fields = fields.split(",")
    for field in range(1, len(fields)): data.append([])

    # Generate each series from retrieved records 
    for record in records:
        local_time = datetime.strptime(record["Date"], "%Y-%m-%d")
        utc = helpers.local_to_utc(config, local_time).timestamp()

        # Create point and add to relevant series
        for field in range(1, len(fields)):
            point = { "x": utc, "y": record[fields[field]] }
            data[field - 1].append(point)
    return flask.jsonify(data)

def data_camera():
    global config
    data = dict.fromkeys(["Time", "ImgP", "SRis", "SSet"])

    # Try parsing time specified in URL
    if flask.request.args.get("time") == None: return flask.jsonify(data)
    try:
        url_time = datetime.strptime(
            flask.request.args.get("time"), "%Y-%m-%dT%H-%M-%S")
    except: return flask.jsonify(data)

    # Get image for that time
    image_path = os.path.join(config.camera_drive,
        url_time.strftime("%Y/%m/%d/%Y-%m-%dT%H-%M-%S") + ".jpg")

    # Go back five minutes if no image and not in absolute mode
    if not os.path.isfile(image_path):
        if not flask.request.args.get("abs") == "1":
            url_time -= timedelta(minutes = 5)
            image_path = os.path.join(config.camera_drive,
                url_time.strftime("%Y/%m/%d/%Y-%m-%dT%H-%M-%S") + ".jpg")

            if os.path.isfile(image_path): 
                data["ImgP"] = ("data/camera/"
                    + url_time.strftime("%Y/%m/%d/%Y-%m-%dT%H-%M-%S") + ".jpg")
            else: url_time += timedelta(minutes = 5)

    else: data["ImgP"] = ("data/camera/"
        + url_time.strftime("%Y/%m/%d/%Y-%m-%dT%H-%M-%S") + ".jpg")

    # Calculate sunrise and sunset times
    location = astral.Location(
        ("", "", config.aws_latitude, config.aws_longitude, "UTC",
         config.aws_elevation))
    solar = location.sun(date = url_time, local = False)
    
    data["SRis"] = solar["sunrise"].strftime("%Y-%m-%d %H:%M:%S")
    data["SSet"] = solar["sunset"].strftime("%Y-%m-%d %H:%M:%S")
    data["Noon"] = solar["noon"].strftime("%Y-%m-%d %H:%M:%S")
    
    data["Time"] = url_time.strftime("%Y-%m-%d %H:%M:%S")
    return flask.jsonify(data)

def file_camera(year, month, day, file_name):
    return flask.send_from_directory(os.path.join(config.camera_drive, year,
        month, day), file_name)

def data_about():
    global config, startup_time
    data = dict.fromkeys(["Time", "STim", "EncT", "CPUT", "IDRS", "CDRS"])

    # Try parsing time specified in URL
    if flask.request.args.get("time") == None: return flask.jsonify(data)
    try:
        url_time = datetime.strptime(
            flask.request.args.get("time"), "%Y-%m-%dT%H-%M-%S")
    except: return flask.jsonify(data)

    # Get record for that time
    record = analysis.record_for_time(config, url_time, DbTable.ENVREPORTS)

    if record != False:
        if record == None:
            # Go back a minute if no record and not in absolute mode
            if not flask.request.args.get("abs") == "1":
                url_time -= timedelta(minutes = 1)
                record = analysis.record_for_time(config, url_time,
                                                  DbTable.ENVREPORTS)
                
                if record != False:
                    if record != None:
                        # Add record data to final data
                        for key in dict(zip(record.keys(), record)):
                            if key in data: data[key] = record[key]
                    else: url_time += timedelta(minutes = 1)
                else: url_time += timedelta(minutes = 1)
                    
        else:
            # Add record data to final data
            for key in dict(zip(record.keys(), record)):
                if key in data: data[key] = record[key]

    # Format software startup time
    data["STim"] = startup_time.strftime("%Y-%m-%d %H:%M:%S")
    
    # Get remaining internal storage space
    data["IDRS"] = helpers.remaining_space("/")
    if data["IDRS"] != None: data["IDRS"] = round(data["IDRS"], 2)

    # Get remaining camera storage space
    if config.camera_logging == True:
        data["CDRS"] = helpers.remaining_space(config.camera_drive)
        if data["CDRS"] != None: data["CDRS"] = round(data["CDRS"], 2)
    else: data["CDRS"] = False

    data["Time"] = url_time.strftime("%Y-%m-%d %H:%M:%S")
    return flask.jsonify(data)

def ctrl_command():
    if flask.request.args.get("cmd") == None: return

    if flask.request.args.get("cmd") == "shutdown": do_shutdown(None)
    elif flask.request.args.get("cmd") == "restart": do_restart(None)
    else: return
    

# ENTRY POINT ==================================================================
def entry_point():
    global config, startup_time; config.load()

    if len(sys.argv) == 2:
        startup_time = datetime.strptime(sys.argv[1], "%Y-%m-%dT%H:%M:%S")
    else: startup_time = datetime.utcnow()

    # SETUP POWER BUTTONS ------------------------------------------------------
    gpio.setwarnings(False); gpio.setmode(gpio.BCM)
    gpio.setup(17, gpio.IN, gpio.PUD_UP)
    gpio.add_event_detect(17, gpio.FALLING, callback = do_shutdown,
                          bouncetime = 300)
    gpio.setup(18, gpio.IN, gpio.PUD_UP)
    gpio.add_event_detect(18, gpio.FALLING, callback = do_restart,
                          bouncetime = 300)

    # -- CREATE SERVER ---------------------------------------------------------
    server = flask.Flask(__name__, static_folder = "server/res",
                         template_folder = "server")

    server.add_url_rule("/", view_func = page_now)
    server.add_url_rule("/index.html", view_func = page_now)
    server.add_url_rule("/statistics.html", view_func = page_statistics)
    server.add_url_rule("/graph-day.html", view_func = page_graph_day)
    server.add_url_rule("/graph-year.html", view_func = page_graph_year)
    server.add_url_rule("/camera.html", view_func = page_camera)
    server.add_url_rule("/about.html", view_func = page_about)

    server.add_url_rule("/data/now.json", view_func = data_now)
    server.add_url_rule("/data/statistics.json", view_func = data_statistics)
    server.add_url_rule("/data/graph-day.json", view_func = data_graph_day)
    server.add_url_rule("/data/graph-year.json", view_func = data_graph_year)
    server.add_url_rule("/data/camera.json", view_func = data_camera)
    server.add_url_rule("/data/camera/<year>/<month>/<day>/<file_name>",
        view_func = file_camera)
    server.add_url_rule("/data/about.json", view_func = data_about)
    server.add_url_rule("/ctrl/command", view_func = ctrl_command)

    # -- START SERVER ----------------------------------------------------------
    server.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0
    logging.getLogger("werkzeug").setLevel(logging.CRITICAL)
    threading.Thread(target = 
        lambda: server.run(host = "0.0.0.0", threaded = True)).start()

    # Prevent main thread from ending, to sustain interrupt monitoring
    while True: time.sleep(900)

if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.realpath(__file__))
    with daemon.DaemonContext(working_directory = current_dir):
        entry_point()
