import sqlite3

from frames import DbTable

def record_for_time(config, time, table):
    time = time.replace(second = 0, microsecond = 0)
        
    try:
        with sqlite3.connect(config.database_path) as database:
            database.row_factory = sqlite3.Row
            cursor = database.cursor()

            # Query respective database table
            if table == DbTable.UTCREPORTS:
                cursor.execute("SELECT * FROM utcReports WHERE Time = ?",
                               (time.strftime("%Y-%m-%d %H:%M:%S"),))

            elif table == DbTable.UTCENVIRON:
                cursor.execute("SELECT * FROM utcEnviron WHERE Time = ?",
                               (time.strftime("%Y-%m-%d %H:%M:%S"),))

            elif table == DbTable.LOCALSTATS:
                cursor.execute("SELECT * FROM localStats WHERE Date = ?",
                               (time.strftime("%Y-%m-%d"),))

            return cursor.fetchone()
    except: return False

def stats_for_range(config, start, end, table):
    start = start.replace(second = 0, microsecond = 0)
    end = end.replace(second = 0, microsecond = 0)

    try:
        with sqlite3.connect(config.database_path) as database:
            database.row_factory = sqlite3.Row
            cursor = database.cursor()

            # Query respective database table
            if table == DbTable.UTCREPORTS:
                cursor.execute("SELECT min(AirT), max(AirT), avg(AirT), "
                    + "min(RelH), max(RelH), avg(RelH), min(DewP), max(DewP), "
                    + "avg(DewP), min(WSpd), max(WSpd), avg(WSpd), min(WDir), "
                    + "max(WDir), avg(WDir), min(WGst), max(WGst), avg(WGst), "
                    + "sum(SunD), sum(Rain), min(MSLP), max(MSLP), avg(MSLP), "
                    + "min(ST10), max(ST10), avg(ST10), min(ST30), max(ST30), "
                    + "avg(ST30), min(ST00), max(ST00), avg(ST00) FROM "
                    + "utcReports WHERE Time BETWEEN ? AND ?",
                        (start.strftime("%Y-%m-%d %H:%M:%S"),
                         end.strftime("%Y-%m-%d %H:%M:%S")))

            elif table == DbTable.UTCENVIRON:
                cursor.execute("SELECT min(EncT), max(EncT), avg(EncT), "
                    + "min(CPUT), max(CPUT), avg(CPUT) FROM utcEnviron WHERE "
                    + "Time BETWEEN ? AND ?",
                        (start.strftime("%Y-%m-%d %H:%M:%S"),
                         end.strftime("%Y-%m-%d %H:%M:%S")))

            elif table == DbTable.LOCALSTATS:
                cursor.execute("SELECT min(AirT_Min), max(AirT_Max), "
                    + "avg(AirT_Avg), min(RelH_Min), max(RelH_Max), "
                    + "avg(RelH_Avg), min(DewP_Min), max(DewP_Max), "
                    + "avg(DewP_Avg), min(WSpd_Min), max(WSpd_Max), "
                    + "avg(WSpd_Avg), min(WDir_Min), max(WDir_Max), "
                    + "avg(WDir_Avg), min(WGst_Min), max(WGst_Max), "
                    + "avg(WGst_Avg), sum(SunD_Ttl), sum(Rain_Ttl), "
                    + "min(MSLP_Min), max(MSLP_Max), avg(MSLP_Avg), "
                    + "min(ST10_Min), max(ST10_Max), avg(ST10_Avg), "
                    + "min(ST30_Min), max(ST30_Max), avg(ST30_Avg), "
                    + "min(ST00_Min), max(ST00_Max), avg(ST00_Avg) FROM "
                    + "localStats WHERE Date BETWEEN ? AND ?",
                        (start.strftime("%Y-%m-%d"),
                         start.strftime("%Y-%m-%d")))

            return cursor.fetchone()
    except: return False