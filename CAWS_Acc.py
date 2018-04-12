""" CAWS Data Access Program
      Responsible for enabling access to and control of the station, and for
      serving its data to devices accessing from within the local network
"""

# DEPENDENCIES -----------------------------------------------------------------
import time
from datetime import datetime, timedelta

import flask

# MESSAGE ----------------------------------------------------------------------
print("--- Custom Automatic Weather Station ---")
print("Program: Data Access Software")
print("Author:  Henry Hunt")
print("Version: V4.0 (April 2018)")
print("")
print("----------- DO NOT TERMINATE -----------")

# GLOBAL VARIABLES -------------------------------------------------------------
start_time = None

# PAGE SERVERS -----------------------------------------------------------------
def page_now():
      return "Now"

def page_statistics():
      return "Statistics"

def page_graph_day():
      return "Graph Day"

def page_graph_month():
      return "Graph Month"

def page_graph_year():
      return "Graph Year"

def page_camera():
      return "Camera"

def page_about():
      return "About"


# ENTRY POINT ==================================================================
# -- CREATE SERVER -------------------------------------------------------------
server = flask.Flask(__name__, static_folder = "interface",
                     template_folder = "interface")

# -- ROUTE URLS ----------------------------------------------------------------
server.add_url_rule("/", "", page_now)
server.add_url_rule("/", "index.html", page_now)
server.add_url_rule("/", "statistics.html", page_statistics)
server.add_url_rule("/", "graph_day.html", page_graph_day)
server.add_url_rule("/", "graph_month.html", page_graph_month)
server.add_url_rule("/", "graph_year.html", page_graph_year)
server.add_url_rule("/", "camera.html", page_camera)
server.add_url_rule("/", "about.html", page_about)

# -- START SERVER --------------------------------------------------------------
start_time = datetime.utcnow().replace(second = 0, microsecond = 0)
server.run(host = "0.0.0.0", port = 80, threaded = True)