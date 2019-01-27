import math

import routines.config as config

def calculate_dew_point(AirT, RelH):
    if AirT == None or RelH == None: return None

    DewP_a = 0.4343 * math.log(RelH / 100)
    DewP_b = ((8.082 - AirT / 556.0) * AirT)
    DewP_c = DewP_a + (DewP_b) / (256.1 + AirT)
    DewP_d = math.sqrt((8.0813 - DewP_c) ** 2 - (1.842 * DewP_c))

    return 278.04 * ((8.0813 - DewP_c) - DewP_d)

def calculate_mean_sea_level_pressure(StaP, AirT, DewP):
    if StaP == None or AirT == None or DewP == None: return None

    MSLP_a = 6.11 * 10 ** ((7.5 * DewP) / (237.3 + DewP))
    MSLP_b = (9.80665 / 287.3) * config.aws_elevation
    MSLP_c = ((0.0065 * config.aws_elevation) / 2) 
    MSLP_d = AirT + 273.15 + MSLP_c + MSLP_a * 0.12
    
    return StaP * math.exp(MSLP_b / MSLP_d)