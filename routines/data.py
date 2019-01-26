import math
from datetime import timedelta
import statistics

import routines.config as config

def prepare_wind_ticks(past_WSpd_ticks, new_WSpd_ticks, ten_mins_ago):
    """ Prepares wind data by merging new and old ticks and removing ticks older
        than ten minutes
    """
    past_WSpd_ticks.extend(new_WSpd_ticks)

    for tick in list(past_WSpd_ticks):
        if tick < ten_mins_ago: past_WSpd_ticks.remove(tick)

def calculate_wind_speed(past_WSpd_ticks, two_mins_ago):
    """ Calculates average wind speed from a list of timed ticks, in three
        second samples
    """
    WSpd_values = []

    # Iterate over data in three second samples
    for second in range(0, 118, 3):
        WSpd_start = two_mins_ago + timedelta(seconds = second)
        WSpd_end = WSpd_start + timedelta(seconds = 3)
        ticks_in_WSpd_sample = 0

        # Calculate three second average wind speed
        for tick in past_WSpd_ticks:
            if tick >= WSpd_start and tick < WSpd_end:
                ticks_in_WSpd_sample += 1

        WSpd_values.append((ticks_in_WSpd_sample * 2.5) / 3)
    return statistics.mean(WSpd_values)

def calculate_wind_direction(past_WDir_samples, new_WDir_samples, two_mins_ago):
    """ Calculates average wind direction from a list of timed samples
    """
    # Merge new and old samples and remove samples older than two mins
    past_WDir_samples.extend(new_WDir_samples)

    for sample in list(past_WDir_samples):
        if sample[0] < two_mins_ago: past_WDir_samples.remove(sample)

    if len(past_WDir_samples) == 0: return None
        
    WDir_total = 0
    for sample in past_WDir_samples: WDir_total += sample[1]

    return WDir_total / len(past_WDir_samples)

def calculate_wind_gust(past_WSpd_ticks, ten_mins_ago):
    """ Calculates the maximum three second wind speed from a list of ticks
    """
    WGst_value = 0

    # Iterate over each second in three second samples
    for second in range(0, 598):
        WGst_start = ten_mins_ago + timedelta(seconds = second)
        WGst_end = WGst_start + timedelta(seconds = 3)
        ticks_in_WGst_sample = 0

        # Calculate 3 second average wind speed, check if highest
        for tick in past_WSpd_ticks:
            if tick >= WGst_start and tick < WGst_end:
                ticks_in_WGst_sample += 1

        WGst_sample = (ticks_in_WGst_sample * 2.5) / 3
        if WGst_sample > WGst_value: WGst_value = WGst_sample
        
    return WGst_value

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