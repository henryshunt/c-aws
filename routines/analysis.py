from datetime import timedelta

import sqlite3

import routines.config as config
from routines.frames import DbTable
import routines.queries as queries
import routines.helpers as helpers

def record_for_time(time, table):
    """ Query the database for a record in the specified table matching the
        specified time
    """
    time = time.replace(second = 0, microsecond = 0)
        
    try:
        with sqlite3.connect(config.database_path) as database:
            database.row_factory = sqlite3.Row
            cursor = database.cursor()

            # Query respective database table
            if table == DbTable.REPORTS:
                cursor.execute(queries.SELECT_SINGLE_REPORT,
                               (time.strftime("%Y-%m-%d %H:%M:%S"),))

            elif table == DbTable.ENVREPORTS:
                cursor.execute(queries.SELECT_SINGLE_ENVREPORT,
                               (time.strftime("%Y-%m-%d %H:%M:%S"),))

            elif table == DbTable.DAYSTATS:
                cursor.execute(queries.SELECT_SINGLE_DAYSTAT,
                               (time.strftime("%Y-%m-%d"),))

            return cursor.fetchone()
    except: return False

def stats_for_date(local_time):
    """ Calculate statistics using the reports table, for the date corresponding
        to the specified local time
    """
    try:
        bounds = helpers.day_bounds_utc(local_time, False)
        
        with sqlite3.connect(config.database_path) as database:
            database.row_factory = sqlite3.Row
            cursor = database.cursor()

            # Generate the statistics
            cursor.execute(queries.GENERATE_DAYSTAT,
                           (bounds[0].strftime("%Y-%m-%d %H:%M:%S"),
                            bounds[1].strftime("%Y-%m-%d %H:%M:%S"),
                            (bounds[0] + timedelta(
                                minutes = 1)).strftime("%Y-%m-%d %H:%M:%S"),
                            (bounds[1] + timedelta(
                                minutes = 1)).strftime("%Y-%m-%d %H:%M:%S")))
                            
            return cursor.fetchone()
    except: return False