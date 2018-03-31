import sqlite3

from frames import DbTable

def record_for_time(config, time, table):
    try:
        time = time.replace(second = 0, microsecond = 0)
        
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
    try:
        start = start.replace(second = 0, microsecond = 0)
        end = end.replace(second = 0, microsecond = 0)
        
        with sqlite3.connect(config.database_path) as database:
            database.row_factory = sqlite3.Row
            cursor = database.cursor()

            # Query respective database table
            if table == DbTable.UTCREPORTS:
                cursor.execute("SELECT min(AirT), max(AirT), avg(AirT), "
                                    + "min(RelH), max(RelH), avg(RelH), "
                                    + "min(DewP), max(DewP), avg(DewP), "
                                    + "min(WSpd), max(WSpd), avg(WSpd), "
                                    + "min(WDir), max(WDir), avg(WDir), "
                                    + "min(WGst), max(WGst), avg(WGst), "
                                    + "total(SunD), total(Rain), "
                                    + "min(MSLP), max(MSLP), avg(MSLP), "
                                    + "min(ST10), max(ST10), avg(ST10), "
                                    + "min(ST30), max(ST30), avg(ST30), "
                                    + "min(ST00), max(ST00), avg(ST00) "
                                    + " FROM utcReports WHERE Time BETWEEN "
                                    + "? AND ?",
                               (start.strftime("%Y-%m-%d %H:%M:%S"),
                                end.strftime("%Y-%m-%d %H:%M:%S")))
            elif table == DbTable.UTCENVIRON:
                cursor.execute("SELECT min(EncT), max(EncT), avg(EncT), "
                                    + "min(CPUT), max(CPUT), avg(CPUT) "
                                    + "FROM utcEnviron WHERE Time BETWEEN "
                                    + "? AND ?",
                               (start.strftime("%Y-%m-%d %H:%M:%S"),
                                end.strftime("%Y-%m-%d %H:%M:%S")))
            elif table == DbTable.LOCALSTATS:
                cursor.execute("SELECT * FROM localStats WHERE Date BETWEEN "
                                    + "? AND ?",
                               (start.strftime("%Y-%m-%d"),
                               start.strftime("%Y-%m-%d")))

            return cursor.fetchone()
    except: return False