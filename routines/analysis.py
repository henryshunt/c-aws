from datetime import timedelta

import sqlite3

import routines.config as config
from routines.frames import DbTable
import routines.queries as queries
import routines.helpers as helpers

def record_for_time(time, table):
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

def fields_in_range(start, end, fields, table):
    start = start.replace(second = 0, microsecond = 0)
    end = end.replace(second = 0, microsecond = 0)

    try:
        with sqlite3.connect(config.database_path) as database:
            database.row_factory = sqlite3.Row
            cursor = database.cursor()

            # Query respective database table
            if table == DbTable.REPORTS:
                if ("AirT" in fields or "RelH" in fields or "DewP" in fields or
                    "WSpd" in fields or "WDir" in fields or "WGst" in fields or
                    "SunD" in fields or "Rain" in fields or "StaP" in fields or
                    "MSLP" in fields):

                    cursor.execute(queries.SELECT_FIELDS_REPORTS
                                .format(fields),
                                ((start + timedelta(
                                    minutes = 1)).strftime("%Y-%m-%d %H:%M:%S"),
                                 (end + timedelta(minutes = 1))
                                    .strftime("%Y-%m-%d %H:%M:%S")))
                else:
                    cursor.execute(queries.SELECT_FIELDS_REPORTS
                                .format(fields),
                                (start.strftime("%Y-%m-%d %H:%M:%S"),
                                 end.strftime("%Y-%m-%d %H:%M:%S")))

            elif table == DbTable.ENVREPORTS:
                cursor.execute(queries.SELECT_FIELDS_ENVREPORTS
                               .format(fields),
                               (start.strftime("%Y-%m-%d %H:%M:%S"),
                                end.strftime("%Y-%m-%d %H:%M:%S")))

            elif table == DbTable.DAYSTATS:
                cursor.execute(queries.SELECT_FIELDS_DAYSTATS
                               .format(fields),
                               (start.strftime("%Y-%m-%d"),
                                end.strftime("%Y-%m-%d")))

            return cursor.fetchall()
    except: return False

def stats_for_date(local_time):
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

def stats_for_year(year):
    try:
        with sqlite3.connect(config.database_path) as database:
            database.row_factory = sqlite3.Row
            cursor = database.cursor()

            # Generate the statistics
            cursor.execute(queries.GENERATE_YEAR_STATS,
                           (year,))
                            
            return cursor.fetchone()
    except: return False

def stats_for_months(year):
    try:
        with sqlite3.connect(config.database_path) as database:
            database.row_factory = sqlite3.Row
            cursor = database.cursor()

            # Generate the statistics
            cursor.execute(queries.GENERATE_MONTHS_STATS,
                           (year,))
                            
            return cursor.fetchall()
    except: return False

def past_hour_total(now, column):
    start = now.replace(second = 0, microsecond = 0) - timedelta(minutes = 59)
    end = now.replace(second = 0, microsecond = 0)

    try:
        with sqlite3.connect(config.database_path) as database:
            database.row_factory = sqlite3.Row
            cursor = database.cursor()

            cursor.execute(queries.SELECT_PAST_HOUR_REPORTS
                           .format(column),
                           (start.strftime("%Y-%m-%d %H:%M:%S"),
                            end.strftime("%Y-%m-%d %H:%M:%S")))

            return cursor.fetchone()
    except: return False