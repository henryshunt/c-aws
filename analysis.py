import sqlite3

from frames import DbTable

def record_for_time(config, utc, table):
    try:
        utc = utc.replace(second = 0, microsecond = 0)
        
        with sqlite3.connect(config.database_path) as database:
            database.row_factory = sqlite3.Row
            cursor = database.cursor()

            # Query respective database table
            if table == DbTable.UTCREPORTS:
                cursor.execute("SELECT * FROM utcReports WHERE utc = ?", (utc.strftime("%Y-%m-%d %H:%M:%S"),))
            elif table == DbTable.UTCENVIRON:
                cursor.execute("SELECT * FROM utcEnviron WHERE utc = ?", (utc.strftime("%Y-%m-%d %H:%M:%S"),))
            elif table == DbTable.LOCALSTATS:
                cursor.execute("SELECT * FROM localStats WHERE utc = ?", (utc.strftime("%Y-%m-%d"),))

            return cursor.fetchone()
    except: return False