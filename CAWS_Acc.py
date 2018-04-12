""" CAWS Data Access Program
      Responsible for enabling access to and control of the station, and for
      serving its data to devices accessing from within the local network
"""

# DEPENDENCIES -----------------------------------------------------------------
import time
from datetime import datetime, timedelta

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
    AirT = "No Data"; ExpT = "No Data"; RelH = "No Data"; DewP = "No Data"
    WSpd = "No Data"; WDir = "No Data"; WGst = "No Data"; SunD = "No Data"
    Rain = "No Data"; StaP = "No Data"; MSLP = "No Data"; PTen = "No Data"
    ST10 = "No Data"; ST30 = "No Data"; ST00 = "No Data"
    SunD_Phr = "No Data"; Rain_Phr = "No Data"

    utc = datetime.now().replace(second = 0, microsecond = 0)
    record = analysis.record_for_time(config, utc, DbTable.UTCREPORTS)

    # Try previous minute if no record for current minute
    if record == False or record == None:
        utc -= timedelta(minutes = 1)
        record = analysis.record_for_time(config, utc, DbTable.UTCREPORTS)

        # Return to current minute if no record for previous minute
        if record == False or record == None:
              utc += timedelta(minutes = 1)
            
    local_time = helpers.utc_to_local(config, utc).strftime("%H:%M")

    # get values to display for each report parameter
    if record != False and record != None:
        if record["AirT"] != None: AirT = str(record["AirT"]) + "°C"
        if record["ExpT"] != None: ExpT = str(record["ExpT"]) + "°C"
        if record["RelH"] != None: RelH = str(record["RelH"]) + "%"
        if record["DewP"] != None: DewP = str(record["DewP"]) + "°C"
        if record["WSpd"] != None: WSpd = str(record["WSpd"]) + " mph"
        
        if record["wdir"] != None:
            wdir_compass = helpers.degrees_to_compass(record["WDir"])
            WDir = str(record["WDir"]) + "° (" + wdir_compass + ")"
            
        if record["WGst"] != None: WGst = str(record["WGst"]) + " mph"
        if record["SunD"] != None: SunD = str(record["SunD"]) + " sec"
        if record["Rain"] != None: Rain = str(record["Rain"]) + " mm"
        if record["StaP"] != None: StaP = str(record["StaP"]) + " hPa"
        if record["MSLP"] != None: MSLP = str(record["MSLP"]) + " hPa"

        if record["PTen"] != None:
            if float(record["PTen"]) > 0:
                PTen = "+" + str(record["PTen"]) + " hPa"
            else: PTen = str(record["PTen"]) + " hPa"

        if record["ST10"] != None: ST10 = str(record["ST10"]) + "°C"
        if record["ST30"] != None: ST30 = str(record["ST30"]) + "°C"
        if record["ST00"] != None: ST00 = str(record["ST00"]) + "°C"

    # calculate rain over past hour
    # reports_past_hour = analysis.records_in_range(rain_time - timedelta(
    #     hours = 1), rain_time, "reports")

    # if reports_past_hour != None:
    #     rain_past_hour = analysis.calculate_total(reports_past_hour, "rain")
    #     if rain_past_hour != None: rain_phr = str(rain_past_hour) + " mm"

    # render page with data
    return flask.render_template("index.html",
                                 caws_name = config.caws_name,
                                 caws_location = config.caws_location,
                                 AirT = AirT, ExpT = ExpT, RelH = RelH,
                                 DewP = DewP, WSpd = WSpd, WDir = WDir,
                                 WGst = WGst, Rain = Rain, StaP = StaP,
                                 MSLP = MSLP, PTen = PTen, ST10 = ST10,
                                 ST30 = ST30, ST00 = ST00,
                                 SunD_Phr = SunD_Phr, Rain_Phr = Rain_Phr,
                                 data_time = local_time)

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
# -- LOAD CONFIG ---------------------------------------------------------------
config = ConfigData()
config.load()

# -- CREATE SERVER -------------------------------------------------------------
server = flask.Flask(__name__, static_folder = "server",
                     template_folder = "server")

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
server.run(host = "0.0.0.0", threaded = True)
