""" C-AWS Data Access Program
      Responsible for enabling station control and local data viewing
"""

# DEPENDENCIES -----------------------------------------------------------------
import time
from datetime import datetime, timedelta
import os
import sys
import logging

import daemon
import flask

import analysis
import helpers
from config import ConfigData
from frames import DbTable

# GLOBAL VARIABLES -------------------------------------------------------------
config = ConfigData()
startup_time = None

# PAGE SERVERS -----------------------------------------------------------------
def page_now():
    return flask.render_template("index.html",
                                 aws_title = config.aws_location.split(",")[0],
                                 aws_location = config.aws_location)

def page_statistics():
    return flask.render_template("statistics.html",
                                 aws_title = config.aws_location.split(",")[0],
                                 aws_location = config.aws_location)

def page_graph_day():
    return flask.render_template("graph-day.html",
                                 aws_title = config.aws_location.split(",")[0],
                                 aws_location = config.aws_location)

def page_graph_month():
    return flask.render_template("graph-month.html",
                                 aws_title = config.aws_location.split(",")[0],
                                 aws_location = config.aws_location)

def page_graph_year():
    return flask.render_template("graph-year.html",
                                 aws_title = config.aws_location.split(",")[0],
                                 aws_location = config.aws_location)

def page_camera():
    return flask.render_template("camera.html",
                                 aws_title = config.aws_location.split(",")[0],
                                 aws_location = config.aws_location)

def page_about():
    return flask.render_template("about.html",
                                 aws_title = config.aws_location.split(",")[0],
                                 aws_location = config.aws_location,
                                 aws_time_zone = config.aws_time_zone,
                                 aws_elevation = config.aws_elevation,
                                 aws_latitude = config.aws_latitude,
                                 aws_longitude = config.aws_longitude)

# DATA PAGE SERVERS ------------------------------------------------------------
def data_now():
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
        data["SunD_PHr"] = str(timedelta(seconds = SunD_PHr_record["SunD"]))

    # Calculate total rainfall over past hour
    Rain_PHr_record = analysis.past_hour_total(config, url_time, "Rain")
    if Rain_PHr_record != False and Rain_PHr_record != None:
        data["Rain_PHr"] = round(Rain_PHr_record["Rain"], 2)

    # Calculate three hour pressure tendency
    if data["StaP"] != None:
        StaP_PTH_record = analysis.record_for_time(config,
            url_time - timedelta(hours = 3), DbTable.REPORTS)
    
        if StaP_PTH_record != False and StaP_PTH_record != None:
            if StaP_PTH_record["StaP"] != None:
                data["StaP_PTH"] = data["StaP"] - StaP_PTH_record["StaP"]

    # Localise data time
    data["Time"] = helpers.utc_to_local(
        config, url_time).strftime("%Y-%m-%d %H:%M:%S")
    return flask.jsonify(data)

def data_statistics():
    data = dict.fromkeys(["Date", "AirT_Min", "AirT_Max", "AirT_Avg",
                          "RelH_Min", "RelH_Max", "RelH_Avg", "DewP_Min",
                          "DewP_Max", "DewP_Avg", "WSpd_Min", "WSpd_Max",
                          "WSpd_Avg", "WDir_Min", "WDir_Max", "WDir_Avg",
                          "WGst_Min", "WGst_Max", "WGst_Avg", "SunD_Ttl",
                          "Rain_Ttl", "MSLP_Min", "MSLP_Max", "MSLP_Avg",
                          "ST10_Min", "ST10_Max", "ST10_Avg", "ST30_Min",
                          "ST30_Max", "ST30_Avg", "ST00_Min", "ST00_Max",
                          "ST00_Avg", "SLft", "SRgt"])

    # Try parsing time specified in URL
    if flask.request.args.get("date") == None: return flask.jsonify(data)
    try:
        url_time = datetime.strptime(
            flask.request.args.get("date"), "%Y-%m-%d")
    except: return flask.jsonify(data)

    # Get record for that time
    record = analysis.record_for_time(config, url_time, DbTable.DAYSTATS)

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

    data["SLft"] = (url_time - timedelta(days = 1)).strftime("%Y-%m-%d")
    data["Date"] = url_time.strftime("%Y-%m-%d")
    data["SRgt"] = (url_time + timedelta(days = 1)).strftime("%Y-%m-%d")
    return flask.jsonify(data)


def data_graph_day():
    return flask.jsonify(None)

def data_graph_month():
    return flask.jsonify(None)

def data_graph_year():
    return flask.jsonify(None)


def data_camera():
    return flask.jsonify(None)

def data_about():
    global startup_time
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
    data["STim"] = (helpers.utc_to_local(config, startup_time)
                   .strftime("%d/%m/%Y at %H:%M:%S"))
    
    # Get remaining internal storage space
    data["IDRS"] = helpers.remaining_space("/")
    if data["IDRS"] != None: data["IDRS"] = round(data["IDRS"], 2)

    # Get remaining camera storage space
    if config.camera_logging == True:
        data["CDRS"] = helpers.remaining_space(config.camera_drive)
        if data["CDRS"] != None: data["CDRS"] = round(data["CDRS"], 2)
    else: data["CDRS"] = False

    # Localise data time
    data["Time"] = helpers.utc_to_local(
        config, url_time).strftime("%Y-%m-%d %H:%M:%S")
    return flask.jsonify(data)


def do_power_cmd(command):
    time.sleep(5)
    if command == "shutdown": os.system("shutdown -h now")
    elif command == "restart": os.system("shutdown -r now")

def ctrl_command(command):
    do_power_cmd(command)
    return flask.redirect("about.html")

# ENTRY POINT ==================================================================
def entry_point():
    global config, startup_time; config.load()

    if len(sys.argv) == 2:
        startup_time = datetime.strptime(sys.argv[1], "%Y-%m-%dT%H:%M:%S")
    else: startup_time = datetime.utcnow()

    # -- CREATE SERVER ---------------------------------------------------------
    server = flask.Flask(__name__, static_folder = "server/res",
                         template_folder = "server")

    server.add_url_rule("/", view_func = page_now)
    server.add_url_rule("/index.html", view_func = page_now)
    server.add_url_rule("/statistics.html", view_func = page_statistics)
    server.add_url_rule("/graph_day.html", view_func = page_graph_day)
    server.add_url_rule("/graph_month.html", view_func = page_graph_month)
    server.add_url_rule("/graph_year.html", view_func = page_graph_year)
    server.add_url_rule("/camera.html", view_func = page_camera)
    server.add_url_rule("/about.html", view_func = page_about)

    server.add_url_rule("/data/now.json", view_func = data_now)
    server.add_url_rule("/data/statistics.json", view_func = data_statistics)
    server.add_url_rule("/data/graph-day.json", view_func = data_graph_day)
    server.add_url_rule("/data/graph-month.json", view_func = data_graph_month)
    server.add_url_rule("/data/graph-year.json", view_func = data_graph_year)
    server.add_url_rule("/data/camera/<file_name>", view_func = data_camera)
    server.add_url_rule("/data/about.json", view_func = data_about)
    server.add_url_rule("/ctrl/<command>", view_func = ctrl_command)

    # -- START SERVER ----------------------------------------------------------
    server.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0
    logging.getLogger("werkzeug").setLevel(logging.CRITICAL)
    server.run(host = "0.0.0.0", threaded = True)

if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.realpath(__file__))
    with daemon.DaemonContext(working_directory = current_dir):
        entry_point()