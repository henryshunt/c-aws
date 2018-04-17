""" CAWS Data Access Program
      Responsible for enabling access to and control of the station, and for
      serving its data to devices accessing from within the local network
"""

# DEPENDENCIES -----------------------------------------------------------------
import time
from datetime import datetime, timedelta
import os
import sys
import subprocess

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
program_start = None

# PAGE SERVERS -----------------------------------------------------------------
def page_now():
    AirT = "no data"; ExpT = "no data"; RelH = "no data"; DewP = "no data"
    WSpd = "no data"; WDir = "no data"; WGst = "no data"; SunD = "no data"
    SunD_Phr = "no data"; Rain = "no data"; Rain_Phr = "no data"
    StaP = "no data"; MSLP = "no data"; PTen = "no data"; ST10 = "no data"
    ST30 = "no data"; ST00 = "no data"

    utc = datetime.utcnow(); utc_second = utc.second
    utc = utc.replace(second = 0, microsecond = 0)
    record = analysis.record_for_time(config, utc, DbTable.UTCREPORTS)

    # Try previous minute if no record for current minute
    if record == False or record == None and utc_second < 8:
        utc -= timedelta(minutes = 1)
        record = analysis.record_for_time(config, utc, DbTable.UTCREPORTS)

        # Return to current minute if no record for previous minute
        if record == False or record == None:
              utc += timedelta(minutes = 1)
            
    data_time = helpers.utc_to_local(config, utc).strftime("%H:%M")

    # Get values to display for each report parameter
    if record != False and record != None:
        if record["AirT"] != None: AirT = str(record["AirT"]) + "°C"
        if record["ExpT"] != None: ExpT = str(record["ExpT"]) + "°C"
        if record["RelH"] != None: RelH = str(record["RelH"]) + "%"
        if record["DewP"] != None: DewP = str(record["DewP"]) + "°C"
        if record["WSpd"] != None: WSpd = str(record["WSpd"]) + " mph"
        
        if record["WDir"] != None:
            WDir_compass = helpers.degrees_to_compass(record["WDir"])
            WDir = str(record["WDir"]) + "° (" + WDir_compass + ")"
            
        if record["WGst"] != None: WGst = str(record["WGst"]) + " mph"
        if record["SunD"] != None: SunD = str(record["SunD"]) + " sec"
        if record["Rain"] != None: Rain = str(round(record["Rain"], 2)) + " mm"
        if record["StaP"] != None: StaP = str(record["StaP"]) + " hPa"
        if record["MSLP"] != None: MSLP = str(record["MSLP"]) + " hPa"
        
        if record["PTen"] != None:
            if record["PTen"] > 0:
                PTen = "+" + str(record["PTen"]) + " hPa"
            else: PTen = str(record["PTen"]) + " hPa"
            
        if record["ST10"] != None: ST10 = str(record["ST10"]) + "°C"
        if record["ST30"] != None: ST30 = str(record["ST30"]) + "°C"
        if record["ST00"] != None: ST00 = str(record["ST00"]) + "°C"

    # Calculate total sunshine duration over past hour
    SunD_Phr_record = analysis.past_hour_total(config, utc, "SunD")
    if SunD_Phr_record != False and SunD_Phr_record != None:
        if SunD_Phr_record["SunD"] != None:
            SunD_Phr = str(SunD_Phr_record["SunD"]) + " sec"

    # Calculate total rainfall over past hour
    Rain_Phr_record = analysis.past_hour_total(config, utc, "Rain")
    if Rain_Phr_record != False and Rain_Phr_record != None:
        if Rain_Phr_record["Rain"] != None:
            Rain_Phr = str(round(Rain_Phr_record["Rain"], 2)) + " mm"

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

    utc = datetime.utcnow(); utc_second = utc.second
    utc = utc.replace(second = 0, microsecond = 0)
    override_update = False

    # Check for a local date in the URL
    if flask.request.args.get("date") != None:
        try:
            url_date = datetime.strptime(
                flask.request.args.get("date"), "%Y-%m-%d")
            local_date = helpers.utc_to_local(config, utc)
            
            # Check if date in URL is the same as current date
            if (url_date.strftime("%Y-%m-%d")
                == local_date.strftime("%Y-%m-%d")):

                record = analysis.record_for_time(config, local_date,
                                                DbTable.LOCALSTATS)

                # Override updating to trigger if less than 8 seconds
                if record == False or record == None and utc_second < 8:
                    override_update = True
                else: return flask.redirect(flask.url_for("page_statistics"))

            else:
                utc = helpers.local_to_utc(config, url_date)
                local_time = url_date
                record = analysis.record_for_time(config, url_date,
                                                  DbTable.LOCALSTATS)
        except: return flask.redirect(flask.url_for("page_statistics"))

    else:
        local_time = helpers.utc_to_local(config, utc)
        record = analysis.record_for_time(config, local_time,
                                          DbTable.LOCALSTATS)
        
        # Try previous minute if no image for current minute
        if record == False or record == None and utc_second < 8:
            utc -= timedelta(minutes = 1)
            local_time -= timedelta(minutes = 1)
            record = analysis.record_for_time(config,
                                              local_time, DbTable.LOCALSTATS)

            # Return to current minute if no image for previous minute
            if record == False or record == None:
                utc += timedelta(minutes = 1)
                local_time += timedelta(minutes = 1)

    scroller_prev = (local_time - timedelta(days = 1)).strftime("%Y-%m-%d")
    scroller_time = local_time.strftime("%d/%m/%Y")
    scroller_next = (local_time + timedelta(days = 1)).strftime("%Y-%m-%d")
    data_time = helpers.utc_to_local(config, utc).strftime("%H:%M")
    override_update = str(override_update).lower()

    # Get values to display for each statistic parameter
    if record != False and record != None:
        if record["AirT_Min"] != None: AirT_Min = str(record["AirT_Min"]) + "°C"
        if record["AirT_Max"] != None: AirT_Max = str(record["AirT_Max"]) + "°C"
        if record["AirT_Avg"] != None:
            AirT_Avg = str(round(record["AirT_Avg"], 1)) + "°C"
        if record["RelH_Min"] != None: RelH_Min = str(record["RelH_Min"]) + "%"
        if record["RelH_Max"] != None: RelH_Max = str(record["RelH_Max"]) + "%"
        if record["RelH_Avg"] != None:
            RelH_Avg = str(round(record["RelH_Avg"], 1)) + "%"
        if record["DewP_Min"] != None: DewP_Min = str(record["DewP_Min"]) + "°C"
        if record["DewP_Max"] != None: DewP_Max = str(record["DewP_Max"]) + "°C"
        if record["DewP_Avg"] != None:
            DewP_Avg = str(round(record["DewP_Avg"], 1)) + "°C"
        if record["WSpd_Min"] != None:
            WSpd_Min = str(record["WSpd_Min"]) + " mph"
        if record["WSpd_Max"] != None:
            WSpd_Max = str(record["WSpd_Max"]) + " mph"
        if record["WSpd_Avg"] != None:
            WSpd_Avg = str(round(record["WSpd_Avg"], 1)) + " mph"
        if record["WDir_Min"] != None: WDir_Min = str(record["WDir_Min"]) + "°"
        if record["WDir_Max"] != None: WDir_Max = str(record["WDir_Max"]) + "°"
        if record["WDir_Avg"] != None:
            WDir_Avg = str(round(record["WDir_Avg"])) + "°"
        if record["WGst_Min"] != None:
            WGst_Min = str(record["WGst_Min"]) + " mph"
        if record["WGst_Max"] != None:
            WGst_Max = str(record["WGst_Max"]) + " mph"
        if record["WGst_Avg"] != None:
            WGst_Avg = str(round(record["WGst_Avg"], 1)) + " mph"
        if record["SunD_Ttl"] != None:
            SunD_Ttl = str(record["SunD_Ttl"]) + " sec"
        if record["Rain_Ttl"] != None:
            Rain_Ttl = str(round(record["Rain_Ttl"], 2)) + " mm"
        if record["MSLP_Min"] != None:
            MSLP_Min = str(record["MSLP_Min"]) + " hPa"
        if record["MSLP_Max"] != None:
            MSLP_Max = str(record["MSLP_Max"]) + " hPa"
        if record["MSLP_Avg"] != None:
            MSLP_Avg = str(round(record["MSLP_Avg"], 1)) + " hPa"
        if record["ST10_Min"] != None: ST10_Min = str(record["ST10_Min"]) + "°C"
        if record["ST10_Max"] != None: ST10_Max = str(record["ST10_Max"]) + "°C"
        if record["ST10_Avg"] != None:
            ST10_Avg = str(round(record["ST10_Avg"], 1)) + "°C"
        if record["ST30_Min"] != None: ST30_Min = str(record["ST30_Min"]) + "°C"
        if record["ST30_Max"] != None: ST30_Max = str(record["ST30_Max"]) + "°C"
        if record["ST30_Avg"] != None:
            ST30_Avg = str(round(record["ST30_Avg"], 1)) + "°C"
        
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
                                 data_time = data_time,
                                 override_update = override_update)

def page_graph_day():
    utc = datetime.utcnow().replace(second = 0, microsecond = 0)

    # Check for a local date in the URL
    if flask.request.args.get("date") != None:
        try:
            url_date = datetime.strptime(
                flask.request.args.get("date"), "%Y-%m-%d")

            # Check if date in URL is the same as current date
            if (url_date.strftime("%Y-%m-%d")
                == helpers.utc_to_local(config, utc).strftime("%Y-%m-%d")):
                    return flask.redirect(flask.url_for("page_graph_day"))

            else:
                utc = helpers.local_to_utc(config, url_date)
                local_time = url_date
                bounds = helpers.day_bounds_utc(config, url_date, True)
        except: return flask.redirect(flask.url_for("page_graph_day"))

    else:
        local_time = helpers.utc_to_local(config, utc)
        bounds = helpers.day_bounds_utc(config, local_time, True)
    
    start = bounds[0].strftime("%Y-%m-%dT%H-%M-%S")
    end = bounds[1].strftime("%Y-%m-%dT%H-%M-%S")
    low = helpers.utc_to_local(config, bounds[0]).timestamp()
    high = helpers.utc_to_local(config, bounds[1]).timestamp()

    scroller_prev = (local_time - timedelta(days = 1)).strftime("%Y-%m-%d")
    scroller_time = local_time.strftime("%d/%m/%Y")
    scroller_next = (local_time + timedelta(days = 1)).strftime("%Y-%m-%d")
    data_time = local_time.strftime("%H:%M")

    return flask.render_template("graph_day.html",
                                 caws_name = config.caws_name,
                                 caws_location = config.caws_location,
                                 start = start, end = end,
                                 low = low, high = high,
                                 scroller_prev = scroller_prev,
                                 scroller_time = scroller_time,
                                 scroller_next = scroller_next,
                                 data_time = data_time)

def page_graph_month():
    return flask.render_template("graph_month.html",
                                 caws_name = config.caws_name,
                                 caws_location = config.caws_location)

def page_graph_year():
    utc = datetime.utcnow().replace(second = 0, microsecond = 0)
    local_time = helpers.utc_to_local(config, utc).replace(hour = 0, minute = 0)
    
    end = local_time - timedelta(days = 1)
    start = end - timedelta(days = 365)
    low = helpers.utc_to_local(config, start).timestamp()
    high = helpers.utc_to_local(config, end).timestamp()
    start = start.strftime("%Y-%m-%dT%H-%M-%S")
    end = end.strftime("%Y-%m-%dT%H-%M-%S")

    data_time = local_time.strftime("%H:%M")

    return flask.render_template("graph_year.html",
                                 caws_name = config.caws_name,
                                 caws_location = config.caws_location,
                                 start = start, end = end,
                                 low = low, high = high,
                                 data_time = data_time)

def page_camera():
    utc = datetime.utcnow(); utc_second = utc.second
    utc = helpers.last_five_mins(utc.replace(second = 0, microsecond = 0))
    override_update = False

    # Check for a time in the URL
    if flask.request.args.get("time") != None:
        try:
            url_time = datetime.strptime(
                flask.request.args.get("time"), "%Y-%m-%dT%H-%M")
            local_time = helpers.utc_to_local(config, utc)
            
            # Check if time in URL is the same as current time
            if (url_time.strftime("%Y-%m-%dT%H-%M")
                == local_time.strftime("%Y-%m-%dT%H-%M")):
                
                image_dir = os.path.join(config.camera_drive,
                                            utc.strftime("%Y/%m/%d"))
                image_name = utc.strftime("%Y-%m-%dT%H-%M-%S.jpg")
                
                # Override updating to trigger if less than 8 seconds
                if (not os.path.isfile(os.path.join(image_dir, image_name))
                    and utc_second < 8):
                    
                    override_update = True
                else: return flask.redirect(flask.url_for("page_camera"))
                
            else:
                utc = helpers.local_to_utc(config, url_time)
                local_time = url_time
        except: return flask.redirect(flask.url_for("page_camera"))
        
    else:
        local_time = helpers.utc_to_local(config, utc)
        image_dir = os.path.join(config.camera_drive, utc.strftime("%Y/%m/%d"))
        image_name = utc.strftime("%Y-%m-%dT%H-%M-%S.jpg")
        
        # Try previous 5 mins if no image for current 5 min
        if (not os.path.isfile(os.path.join(image_dir, image_name)) and
            utc_second < 8):
            
                utc -= timedelta(minutes = 5)
                local_time -= timedelta(minutes = 5)
                image_dir = os.path.join(config.camera_drive,
                                         utc.strftime("%Y/%m/%d"))
                image_name = utc.strftime("%Y-%m-%dT%H-%M-%S.jpg")

                # Return to current 5 mins if no image for previous 5 mins
                if not os.path.isfile(os.path.join(image_dir, image_name)):
                    utc += timedelta(minutes = 5)
                    local_time += timedelta(minutes = 5)

    delta = timedelta(minutes = 5)
    scroller_prev = (local_time - delta).strftime("%Y-%m-%dT%H-%M")
    scroller_time = local_time.strftime("%d/%m/%Y %H:%M")
    scroller_next = (local_time + delta).strftime("%Y-%m-%dT%H-%M")
    image_path = "camera/" + local_time.strftime("%Y-%m-%dT%H-%M-%S.jpg")
    data_time = local_time.strftime("%H:%M")
    override_update = str(override_update).lower()

    return flask.render_template("camera.html",
                                 caws_name = config.caws_name,
                                 caws_location = config.caws_location,
                                 scroller_prev = scroller_prev,
                                 scroller_time = scroller_time,
                                 scroller_next = scroller_next,
                                 image_path = image_path,
                                 data_time = data_time,
                                 override_update = override_update)

def page_about():
    startup_time = "no data"; EncT = "no data"; CPUT = "no data"
    internal_space = "no data"; camera_space = "no data"
    backup_space = "no data"

    utc = datetime.utcnow(); utc_second = utc.second
    utc = utc.replace(second = 0, microsecond = 0)
    caws_elevation = str(config.caws_elevation) + " m asl."

    # Format software startup time
    if program_start != None:
        startup_time = (helpers.utc_to_local(config, program_start)
                        .strftime("%d/%m/%Y at %H:%M:%S"))

    # Get computer environment data
    record = analysis.record_for_time(config, utc, DbTable.UTCENVIRON)

    # Try previous minute if no record for current minute
    if record == False or record == None and utc_second < 8:
        utc -= timedelta(minutes = 1)
        record = analysis.record_for_time(config, utc, DbTable.UTCENVIRON)

        # Return to current minute if no record for previous minute
        if record == False or record == None:
              utc += timedelta(minutes = 1)
            
    data_time = helpers.utc_to_local(config, utc).strftime("%H:%M")

    # Get values to display for each environment parameter
    if record != False and record != None:
        if record["EncT"] != None: EncT = str(record["EncT"]) + "°C"
        if record["CPUT"] != None: CPUT = str(record["CPUT"]) + "°C"

    # Get remaining internal storage space
    _internal_space = helpers.remaining_space("/")
    if _internal_space != None:
        internal_space = str(round(_internal_space, 2)) + " gb"

    # Get remaining camera storage space
    if not os.path.isdir(config.camera_drive):
        camera_space = "no drive"
    else:
        _camera_space = helpers.remaining_space(config.camera_drive)
        
        if _camera_space != None:
            camera_space = str(round(_camera_space, 2)) + " gb"

    # Get remaining backup storage space
    if not os.path.isdir(config.backup_drive):
        backup_space = "no drive"
    else:
        _backup_space = helpers.remaining_space(config.backup_drive)
        
        if _backup_space != None:
            backup_space = str(round(_backup_space, 2)) + " gb"
    
    return flask.render_template("about.html",
                                 caws_name = config.caws_name,
                                 caws_location = config.caws_location,
                                 caws_time_zone = config.caws_time_zone,
                                 caws_latitude = config.caws_latitude,
                                 caws_longitude = config.caws_longitude,
                                 caws_elevation = caws_elevation,
                                 startup_time = startup_time,
                                 EncT = EncT, CPUT = CPUT,
                                 internal_space = internal_space,
                                 camera_space = camera_space,
                                 backup_space = backup_space,
                                 data_time = data_time)

def data_camera(file_name):
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

def data_graph():
    try:
        start = datetime.strptime(flask.request.args.get("start"),
                                "%Y-%m-%dT%H-%M-%S")
        end = datetime.strptime(flask.request.args.get("end"),
                                "%Y-%m-%dT%H-%M-%S")

        if flask.request.args.get("table") == "utcReports":
            table = DbTable.UTCREPORTS
        elif flask.request.args.get("table") == "localStats":
            table = DbTable.LOCALSTATS
        else: table = DbTable.UTCENVIRON

        records = analysis.fields_in_range(
            config, start, end, flask.request.args.get("fields"), table)
        
        if records == False: return flask.jsonify([])
        if len(records) == 0: return flask.jsonify([])

        # Create list for each requested database field
        fields = flask.request.args.get("fields").split(",")
        graph_data = []
        for field in range(1, len(fields)): graph_data.append([])

        if table == DbTable.UTCREPORTS:
            if "Rain" in fields: Rain_Ttl = 0
            if "SunD" in fields: SunD_Ttl = 0

        # Generate each series from retrieved records 
        for record in records:
            if fields[0] == "Time":
                time = datetime.strptime(record["Time"], "%Y-%m-%d %H:%M:%S")
            else: time = datetime.strptime(record["Date"], "%Y-%m-%d")

            record_time = helpers.utc_to_local(config, time).timestamp()

            # Create point and add to relevant series
            for field in range(1, len(fields)):
                if table == DbTable.UTCREPORTS:
                    if fields[field] == "Rain":
                        if record[fields[field]] != None:
                            Rain_Ttl += record[fields[field]]
                        point = { "x": record_time, "y": round(Rain_Ttl, 2) }

                    elif fields[field] == "SunD":
                        if record[fields[field]] != None:
                            SunD_Ttl += record[fields[field]]
                        point = { "x": record_time, "y": round(SunD_Ttl, 2) }

                    else:
                        point = { "x": record_time, "y": record[fields[field]] }
                else: point = { "x": record_time, "y": record[fields[field]] }
                    
                graph_data[field - 1].append(point)

        return flask.jsonify(graph_data)
    except: return flask.jsonify([])

def data_command(command):
    current_dir = os.path.dirname(os.path.realpath(__file__))

    if command == "shutdown":
        subprocess.Popen(["python3 " + current_dir + "/power.py -h"],
                         shell = True)
    elif command == "restart":
        subprocess.Popen(["python3 " + current_dir + "/power.py -r"],
                         shell = True)

    return flask.redirect("about.html")


# ENTRY POINT ==================================================================
# -- LOAD CONFIG ---------------------------------------------------------------
config = ConfigData()
if config.load() == False: sys.exit(1)
if config.validate() == False: sys.exit(1)

if len(sys.argv) == 2:
    program_start = datetime.strptime(sys.argv[1], "%Y-%m-%dT%H:%M:%S")
else: program_start = datetime.utcnow()

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

server.add_url_rule("/camera/<file_name>", view_func = data_camera)
server.add_url_rule("/graph/data", view_func = data_graph)
server.add_url_rule("/command/<command>", view_func = data_command)

# -- START SERVER --------------------------------------------------------------
start_time = datetime.utcnow().replace(second = 0, microsecond = 0)
server.run(host = "0.0.0.0", threaded = True)
