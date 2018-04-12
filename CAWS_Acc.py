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
    AirT = "no data"; ExpT = "no data"; RelH = "no data"; DewP = "no data"
    WSpd = "no data"; WDir = "no data"; WGst = "no data"; SunD = "no data"
    Rain = "no data"; StaP = "no data"; MSLP = "no data"; PTen = "no data"
    ST10 = "no data"; ST30 = "no data"; ST00 = "no data"
    SunD_Phr = "no data"; Rain_Phr = "no data"

    utc = datetime.now().replace(second = 0, microsecond = 0)
    phr_time = utc
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
            WDir = "{0:g}".format(record["WDir"]) + "° (" + wdir_compass + ")"
            
        if record["WGst"] != None: WGst = str(record["WGst"]) + " mph"
        if record["SunD"] != None: SunD = str(record["SunD"]) + " sec"
        if record["Rain"] != None:
            Rain = "{0:g}".format(record["Rain"]) + " mm"
        if record["StaP"] != None: StaP = str(record["StaP"]) + " hPa"
        if record["MSLP"] != None: MSLP = str(record["MSLP"]) + " hPa"

        if record["PTen"] != None:
            pten_phrase = helpers.tendency_to_phrase(record["PTen"])
            
            PTen = "+" if record["PTen"] > 0 else ""
            PTen += str(record["PTen"]) + pten_phrase + " hPa"

        if record["ST10"] != None:
            ST10 = "{0:g}".format(record["ST10"]) + "°C"
        if record["ST30"] != None:
            ST30 = "{0:g}".format(record["ST30"]) + "°C"
        if record["ST00"] != None:
            ST00 = "{0:g}".format(record["ST00"]) + "°C"

    # Calculate totals over past hour
    records_phr = analysis.records_in_range(
        config, phr_time - timedelta(hours = 1), phr_time, DbTable.UTCREPORTS)

    if records_phr != False and records_phr != True:
        rain_phr_num = None
        sund_phr_num = None

        # Calculate total sun
        for record in records_phr:
            if record["SunD"] != None:
                if sund_phr_num == None: sund_phr_num = record["sund"]
                else: sund_phr_num += record["SunD"]

        if sund_phr_num != None: SunD_Phr = str(sund_phr_num) + " sec"
        
        # Calculate total rain
        for record in records_phr:
            if record["Rain"] != None:
                if rain_phr_num == None: rain_phr_num = record["Rain"]
                else: rain_phr_num += record["Rain"]

        if rain_phr_num != None: Rain_Phr = "{0:g}".format(rain_phr_num) + " mm"

    # render page with data
    return flask.render_template("index.html",
                                 caws_name = config.caws_name,
                                 caws_location = config.caws_location,
                                 AirT = AirT, ExpT = ExpT, RelH = RelH,
                                 DewP = DewP, WSpd = WSpd, WDir = WDir,
                                 WGst = WGst, SunD = SunD, Rain = Rain,
                                 StaP = StaP, MSLP = MSLP, PTen = PTen,
                                 ST10 = ST10, ST30 = ST30, ST00 = ST00,
                                 SunD_Phr = SunD_Phr, Rain_Phr = Rain_Phr,
                                 data_time = local_time)

def page_statistics():
    AirT_Min = "no data"; AirT_Max = "no data"; AirT_Avg = "no data"
    RelH_Min = "no data"; RelH_Max = "no data"; RelH_Avg = "no data"
    DewP_Min = "no data"; DewP_Max = "no data"; DewP_Avg = "no data"
    WSpd_Min = "no data"; WSpd_Max = "no data"; WSpd_Avg = "no data"
    WDir_Min = "no data"; WDir_Max = "no data"; WDir_Avg = "no data"
    WGst_Min = "no data"; WGst_Max = "no data"; WGst_Avg = "no data"
    SunD_Ttl = "no data"; Rain_Ttl = "no data"
    MSLP_Min = "no data"; MSLP_Max = "no data"; MSLP_Avg = "no data"
    ST10_Min = "no data"; ST10_Max = "no data"; ST10_Avg = "no data"
    ST30_Min = "no data"; ST30_Max = "no data"; ST30_Avg = "no data"
    ST00_Min = "no data"; ST00_Max = "no data"; ST00_Avg = "no data"

    return flask.render_template("statistics.html",
                                 caws_name = config.caws_name,
                                 caws_location = config.caws_location,
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
                                 ST00_Max = ST00_Max, ST00_Avg = ST00_Avg)

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
server.add_url_rule("/index.html", "index.html", page_now)
server.add_url_rule("/statistics.html", "statistics.html", page_statistics)
server.add_url_rule("/graph_day.html", "graph_day.html", page_graph_day)
server.add_url_rule("/graph_month.html", "graph_month.html", page_graph_month)
server.add_url_rule("/graph_year.html", "graph_year.html", page_graph_year)
server.add_url_rule("/camera.html", "camera.html", page_camera)
server.add_url_rule("/about.html", "about.html", page_about)

# -- START SERVER --------------------------------------------------------------
start_time = datetime.utcnow().replace(second = 0, microsecond = 0)
server.run(host = "0.0.0.0", threaded = True)
