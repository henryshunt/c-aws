""" C-AWS Data Access Program
      Responsible for enabling access to and control of the station, and for
      serving its data to devices accessing from within the local network
"""

# DEPENDENCIES -----------------------------------------------------------------
import time
from datetime import datetime, timedelta
import os
import sys
import subprocess
import logging

import flask

import analysis
import helpers
from config import ConfigData
from frames import DbTable

# MESSAGE ----------------------------------------------------------------------
print("--- Custom Automatic Weather Station ---")
print("Program: Access Sub-System")
print("Author:  Henry Hunt")
print("Version: 4C.1 (July 2018)")
print("")
print("----------- DO NOT TERMINATE -----------")

# GLOBAL VARIABLES -------------------------------------------------------------
config = ConfigData()
config.load()

if len(sys.argv) == 2:
    startup_time = datetime.strptime(sys.argv[1], "%Y-%m-%dT%H:%M:%S")
else: startup_time = datetime.utcnow()

# PAGE SERVERS -----------------------------------------------------------------
def page_now():
    return flask.render_template("index.html",
                                 aws_location = config.aws_location)

def page_statistics():
    return flask.render_template("statistics.html",
                                 aws_location = config.aws_location)

def page_graph_day():
    return flask.render_template("graph-day.html",
                                 aws_location = config.aws_location)

def page_graph_month():
    return flask.render_template("graph-month.html",
                                 aws_location = config.aws_location)

def page_graph_year():
    return flask.render_template("graph-year.html",
                                 aws_location = config.aws_location)

def page_camera():
    return flask.render_template("camera.html",
                                 aws_location = config.aws_location)

def page_about():
    return flask.render_template("about.html",
                                 aws_location = config.aws_location)

# DATA PAGE SERVERS ------------------------------------------------------------
def data_now():
    if flask.request.args.get("time") != None:
        try:
            url_time = datetime.strptime(flask.request.args.get("time"),
                                         "%Y-%m-%dT%H-%M-%S")
        except: return "1"
        
        record = analysis.record_for_time(config, url_time, DbTable.UTCREPORTS)

        if record != False:
            if record == None:
                if flask.request.args.get("abs") == "1":
                    return flask.jsonify(None)

                else:
                    record = analysis.record_for_time(config,
                        url_time - timedelta(minutes = 1), DbTable.UTCREPORTS)
                    
                    if record != False:
                        if record != None:
                            record["Time"] = helpers.utc_to_local(config,
                                record["Time"]).strftime("%Y-%m-%d %H:%M:%S")
                            return flask.jsonify(dict(zip(record.keys(),
                                                          record)))
                        else: return flask.jsonify(None)
                    else: return "1"

            else:
                record["Time"] = helpers.utc_to_local(config,
                    record["Time"]).strftime("%Y-%m-%d %H:%M:%S")
                return flask.jsonify(dict(zip(record.keys(), record)))
        else: return "1"

    else: return "1"

def data_statistics():
    if flask.request.args.get("time") != None:
        try:
            url_time = datetime.strptime(flask.request.args.get("time"),
                                         "%Y-%m-%dT%H-%M-%S")
            url_time = helpers.utc_to_local(config, url_time)
        except: return "1"
        
        record = analysis.record_for_time(config, url_time, DbTable.LOCALSTATS)

        if record != False:
            if record == None:
                if flask.request.args.get("abs") == "1":
                    return flask.jsonify(None)

                else: 
                    record = analysis.record_for_time(config,
                        url_time - timedelta(minutes = 1), DbTable.LOCALSTATS)
                    
                    if record != False:
                        if record != None:
                            return flask.jsonify(dict(zip(record.keys(),
                                                          record)))
                        else: return flask.jsonify(None)
                    else: return "1"
            else: return flask.jsonify(dict(zip(record.keys(), record)))
        else: return "1"

    else: return "1"

def data_graph_day():
    return flask.jsonify(None)

def data_graph_month():
    return flask.jsonify(None)

def data_graph_year():
    return flask.jsonify(None)

def data_camera():
    return flask.jsonify(None)

def data_about():
    return flask.jsonify(None)


def ctrl_command():
    return flask.jsonify(None)

# -- CREATE SERVER -------------------------------------------------------------
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

# -- START SERVER --------------------------------------------------------------
server.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0
logging.getLogger("werkzeug").setLevel(logging.CRITICAL)
server.run(host = "0.0.0.0", threaded = True)
