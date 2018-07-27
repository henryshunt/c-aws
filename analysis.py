from datetime import timedelta

import sqlite3

from frames import DbTable
import queries

def record_for_time(config, time, table):
    time = time.replace(second = 0, microsecond = 0)
        
    try:
        with sqlite3.connect(config.database_path) as database:
            database.row_factory = sqlite3.Row
            cursor = database.cursor()

            # Query respective database table
            if table == DbTable.UTCREPORTS:
                cursor.execute(queries.SELECT_SINGLE_UTCREPORTS,
                               (time.strftime("%Y-%m-%d %H:%M:%S"),))

            elif table == DbTable.UTCENVIRON:
                cursor.execute(queries.SELECT_SINGLE_UTCENVIRON,
                               (time.strftime("%Y-%m-%d %H:%M:%S"),))

            elif table == DbTable.LOCALSTATS:
                cursor.execute(queries.SELECT_SINGLE_LOCALSTATS,
                               (time.strftime("%Y-%m-%d"),))

            return cursor.fetchone()
    except: return False

def records_in_range(config, start, end, table):
    start = start.replace(second = 0, microsecond = 0)
    end = end.replace(second = 0, microsecond = 0)

    try:
        with sqlite3.connect(config.database_path) as database:
            database.row_factory = sqlite3.Row
            cursor = database.cursor()

            # Query respective database table
            if table == DbTable.UTCREPORTS:
                cursor.execute(queries.SELECT_RANGE_UTCREPORTS,
                               (start.strftime("%Y-%m-%d %H:%M:%S"),
                                end.strftime("%Y-%m-%d %H:%M:%S")))

            elif table == DbTable.UTCENVIRON:
                cursor.execute(queries.SELECT_RANGE_UTCENVIRON,
                               (start.strftime("%Y-%m-%d %H:%M:%S"),
                                end.strftime("%Y-%m-%d %H:%M:%S")))

            elif table == DbTable.LOCALSTATS:
                cursor.execute(queries.SELECT_RANGE_LOCALSTATS,
                               (start.strftime("%Y-%m-%d"),
                                end.strftime("%Y-%m-%d")))

            return cursor.fetchall()
    except: return False

def fields_in_range(config, start, end, fields, table):
    start = start.replace(second = 0, microsecond = 0)
    end = end.replace(second = 0, microsecond = 0)

    try:
        with sqlite3.connect(config.database_path) as database:
            database.row_factory = sqlite3.Row
            cursor = database.cursor()

            # Query respective database table
            if table == DbTable.UTCREPORTS:
                cursor.execute(queries.SELECT_FIELDS_UTCREPORTS
                               .format(fields),
                               (start.strftime("%Y-%m-%d %H:%M:%S"),
                                end.strftime("%Y-%m-%d %H:%M:%S")))

            elif table == DbTable.UTCENVIRON:
                cursor.execute(queries.SELECT_FIELDS_UTCENVIRON
                               .format(fields),
                               (start.strftime("%Y-%m-%d %H:%M:%S"),
                                end.strftime("%Y-%m-%d %H:%M:%S")))

            elif table == DbTable.LOCALSTATS:
                cursor.execute(queries.SELECT_FIELDS_LOCALSTATS
                               .format(fields),
                               (start.strftime("%Y-%m-%d"),
                                end.strftime("%Y-%m-%d")))

            return cursor.fetchall()
    except: return False

def stats_for_date(config, bounds):
    try:
        with sqlite3.connect(config.database_path) as database:
            database.row_factory = sqlite3.Row
            cursor = database.cursor()

            # Generate the statistics
            cursor.execute(queries.GENERATE_DAYSTAT,
                           (bounds[0].strftime("%Y-%m-%d %H:%M:%S"),
                            bounds[1].strftime("%Y-%m-%d %H:%M:%S")))
                            
            return cursor.fetchone()
    except: return False

def past_hour_total(config, now, column):
    start = now.replace(second = 0, microsecond = 0) - timedelta(minutes = 59)
    end = now.replace(second = 0, microsecond = 0)

    try:
        with sqlite3.connect(config.database_path) as database:
            database.row_factory = sqlite3.Row
            cursor = database.cursor()

            cursor.execute(queries.SELECT_PAST_HOUR_UTCREPORTS
                           .format(column),
                           (start.strftime("%Y-%m-%d %H:%M:%S"),
                            end.strftime("%Y-%m-%d %H:%M:%S")))

            return cursor.fetchone()
    except: return False