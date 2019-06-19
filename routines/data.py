import math
import os

import sqlite3

import routines.config as config
import routines.helpers as helpers

def write_record(query, parameters):
    """ Performs the specified write query using the specified values
    """
    if not os.path.isfile(config.database_path): return False
        
    try:
        free_space = helpers.remaining_space("/")
        if free_space == None or free_space < 0.1: return False
        
        with sqlite3.connect(config.database_path) as database:
            cursor = database.cursor()
            cursor.execute(query, parameters)
            database.commit()

    except: return False
    return True

def calculate_dew_point(AirT, RelH):
    """ Calculates dew point using the same formula the Met Office uses
    """
    if AirT == None or RelH == None: return None

    DewP_a = 0.4343 * math.log(RelH / 100)
    DewP_b = ((8.082 - AirT / 556.0) * AirT)
    DewP_c = DewP_a + (DewP_b) / (256.1 + AirT)
    DewP_d = math.sqrt((8.0813 - DewP_c) ** 2 - (1.842 * DewP_c))

    return 278.04 * ((8.0813 - DewP_c) - DewP_d)

def calculate_mean_sea_level_pressure(StaP, AirT, DewP):
    """ Reduces station pressure to mean sea level using the WMO formula
    """
    if StaP == None or AirT == None or DewP == None: return None

    MSLP_a = 6.11 * 10 ** ((7.5 * DewP) / (237.3 + DewP))
    MSLP_b = (9.80665 / 287.3) * config.aws_elevation
    MSLP_c = ((0.0065 * config.aws_elevation) / 2) 
    MSLP_d = AirT + 273.15 + MSLP_c + MSLP_a * 0.12
    
    return StaP * math.exp(MSLP_b / MSLP_d)