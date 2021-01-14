def generate_write_stats(utc):
    """ Calculates and writes/updates statistics for the specified local day to
        the database
    """
    local = helpers.utc_to_local(utc)
    bounds = helpers.day_bounds_utc(local, False)

    # Calculate new statistics
    QUERY = ("SELECT * FROM (SELECT ROUND(AVG(ST10), 3) AS ST10_Avg, MIN(ST10) "
        + "AS ST10_Min, MAX(ST10) AS ST10_Max, ROUND(AVG(ST30), 3) AS ST30_Avg,"
        + " MIN(ST30) AS ST30_Min, MAX(ST30) AS ST30_Max, ROUND(AVG(ST00), 3) "
        + "AS ST00_Avg, MIN(ST00) AS ST00_Min, MAX(ST00) AS ST00_Max FROM "
        + "reports WHERE Time BETWEEN ? AND ?) INNER JOIN (SELECT "
        + "ROUND(AVG(AirT), 3) AS AirT_Avg, MIN(AirT) AS AirT_Min, MAX(AirT) AS"
        + " AirT_Max, ROUND(AVG(RelH), 3) AS RelH_Avg, MIN(RelH) AS RelH_Min, "
        + "MAX(RelH) AS RelH_Max, ROUND(AVG(DewP), 3) AS DewP_Avg, MIN(DewP) AS"
        + " DewP_Min, MAX(DewP) AS DewP_Max, ROUND(AVG(WSpd), 3) AS WSpd_Avg, "
        + "MIN(WSpd) AS WSpd_Min, MAX(WSpd) AS WSpd_Max, ROUND(AVG(WGst), 3) AS"
        + " WGst_Avg, MIN(WGst) AS WGst_Min, MAX(WGst) AS WGst_Max, SUM(SunD) "
        + "AS SunD_Ttl, ROUND(SUM(Rain), 3) AS Rain_Ttl, ROUND(AVG(MSLP), 3) AS"
        + " MSLP_Avg, MIN(MSLP) AS MSLP_Min, MAX(MSLP) AS MSLP_Max FROM reports"
        + " WHERE Time BETWEEN ? AND ?) INNER JOIN (SELECT ROUND(AVG(WDir)) AS"
        + " WDir_Avg FROM reports WHERE WSpd > 0 AND Time BETWEEN ? AND ?)")

    time_a = (bounds[0] + timedelta(minutes=1)).strftime("%Y-%m-%d %H:%M:%S")
    time_b = (bounds[1] + timedelta(minutes=1)).strftime("%Y-%m-%d %H:%M:%S")

    values = (bounds[0].strftime("%Y-%m-%d %H:%M:%S"),
        bounds[1].strftime("%Y-%m-%d %H:%M:%S"), time_a, time_b, time_a, time_b)

    query = data.query_database(config.main_db_path, QUERY, values)
    if query == False or query == None:
        helpers.data_error("generate_write_stats() 0")
        return
    new_stats = query[0]
    

    # Insert or update statistics in main database
    QUERY_UPDATE = ("UPDATE dayStats SET {0}AirT_Avg = :AirT_Avg, AirT_Min = "
        + ":AirT_Min, AirT_Max = :AirT_Max, RelH_Avg = :RelH_Avg, RelH_Min = "
        + ":RelH_Min, RelH_Max = :RelH_Max, DewP_Avg = :DewP_Avg, DewP_Min = "
        + ":DewP_Min, DewP_Max = :DewP_Max, WSpd_Avg = :WSpd_Avg, WSpd_Min = "
        + ":WSpd_Min, WSpd_Max = :WSpd_Max, WDir_Avg = :WDir_Avg, WGst_Avg = "
        + ":WGst_Avg, WGst_Min = :WGst_Min, WGst_Max = :WGst_Max, SunD_Ttl = "
        + ":SunD_Ttl, Rain_Ttl = :Rain_Ttl, MSLP_Avg = :MSLP_Avg, MSLP_Min = "
        + ":MSLP_Min, MSLP_Max = :MSLP_Max, ST10_Avg = :ST10_Avg, ST10_Min = "
        + ":ST10_Min, ST10_Max = :ST10_Max, ST30_Avg = :ST30_Avg, ST30_Min = "
        + ":ST30_Min, ST30_Max = :ST30_Max, ST00_Avg = :ST00_Avg, ST00_Min = "
        + ":ST00_Min, ST00_Max = :ST00_Max WHERE Date = :Date")
    QUERY_INSERT = ("INSERT OR IGNORE INTO dayStats VALUES (:Date, {0}"
        + ":AirT_Avg, :AirT_Min, :AirT_Max, :RelH_Avg, :RelH_Min, :RelH_Max, "
        + ":DewP_Avg, :DewP_Min, :DewP_Max, :WSpd_Avg, :WSpd_Min, :WSpd_Max, "
        + ":WDir_Avg, :WGst_Avg, :WGst_Min, :WGst_Max, :SunD_Ttl, :Rain_Ttl, "
        + ":MSLP_Avg, :MSLP_Min, :MSLP_Max, :ST10_Avg, :ST10_Min, :ST10_Max, "
        + ":ST30_Avg, :ST30_Min, :ST30_Max, :ST00_Avg, :ST00_Min, :ST00_Max)")

    values = { "AirT_Avg": new_stats["AirT_Avg"],
        "AirT_Min": new_stats["AirT_Min"], "AirT_Max": new_stats["AirT_Max"],
        "RelH_Avg": new_stats["RelH_Avg"], "RelH_Min": new_stats["RelH_Min"], 
        "RelH_Max": new_stats["RelH_Max"], "DewP_Avg": new_stats["DewP_Avg"],
        "DewP_Min": new_stats["DewP_Min"], "DewP_Max": new_stats["DewP_Max"],
        "WSpd_Avg": new_stats["WSpd_Avg"], "WSpd_Min": new_stats["WSpd_Min"],
        "WSpd_Max": new_stats["WSpd_Max"], "WDir_Avg": new_stats["WDir_Avg"],
        "WGst_Avg": new_stats["WGst_Avg"], "WGst_Min": new_stats["WGst_Min"], 
        "WGst_Max": new_stats["WGst_Max"], "SunD_Ttl": new_stats["SunD_Ttl"],
        "Rain_Ttl": new_stats["Rain_Ttl"], "MSLP_Avg": new_stats["MSLP_Avg"],
        "MSLP_Min": new_stats["MSLP_Min"], "MSLP_Max": new_stats["MSLP_Max"],
        "ST10_Avg": new_stats["ST10_Avg"], "ST10_Min": new_stats["ST10_Min"],
        "ST10_Max": new_stats["ST10_Max"], "ST30_Avg": new_stats["ST30_Avg"],
        "ST30_Min": new_stats["ST30_Min"], "ST30_Max": new_stats["ST30_Max"],
        "ST00_Avg": new_stats["ST00_Avg"], "ST00_Min": new_stats["ST00_Min"],
        "ST00_Max": new_stats["ST00_Max"], "Date": local.strftime("%Y-%m-%d") }

    query = data.query_database(
        config.main_db_path, QUERY_UPDATE.format(""), values)
    if query == False:
        helpers.data_error("generate_write_stats() 1")
        return

    query = data.query_database(
        config.main_db_path, QUERY_INSERT.format(""), values)
    if query == False:
        helpers.data_error("generate_write_stats() 2")
        return
    

    # Insert or update statistics in upload database. Random parameter used to
    # ensure every record update is unique
    if config.dayStat_uploading == True:
        values["Signature"] = "".join([random.choice(
            string.ascii_letters + string.digits) for _ in range(6)])

        query = data.query_database(config.upload_db_path,
            QUERY_UPDATE.format("Signature = :Signature, "), values)
        if query == False:
            helpers.data_error("generate_write_stats() 3")
            return

        query = data.query_database(
            config.upload_db_path, QUERY_INSERT.format(":Signature, "), values)
        if query == False:
            helpers.data_error("generate_write_stats() 4")
            return

def operation_generate_stats(utc):
    """ Generates statistics for the local current day from logged records and
        saves them to the database
    """
    local_time = helpers.utc_to_local(utc)

    # Need to recalculate previous day stats once more as averaged and totalled
    # parameters include the first minute of the next day
    if local_time.hour == 0 and local_time.minute == 0:
        generate_write_stats(utc - timedelta(minutes=1))
        
    generate_write_stats(utc)