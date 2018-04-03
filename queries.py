CREATE_UTCREPORTS_TABLE = "CREATE TABLE utcReports (Time TEXT PRIMARY KEY NOT NULL, AirT REAL, ExpT REAL, RelH REAL, DewP REAL, WSpd REAL, WDir INTEGER, WGst REAL, SunD INTEGER, Rain REAL, StaP REAL, PTen REAL, MSLP REAL, ST10 REAL, ST30 REAL, ST00 REAL)"
CREATE_UTCENVIRON_TABLE = "CREATE TABLE utcEnviron (Time TEXT PRIMARY KEY NOT NULL, EncT REAL, CPUT REAL)"
CREATE_LOCALSTATS_TABLE = "CREATE TABLE localStats (Date TEXT PRIMARY KEY NOT NULL, AirT_Min REAL, AirT_Max REAL, AirT_Avg REAL, RelH_Min REAL, RelH_Max REAL, RelH_Avg REAL, DewP_Min REAL, DewP_Max REAL, DewP_Avg REAL, WSpd_Min REAL, WSpd_Max REAL, WSpd_Avg REAL, WDir_Min INTEGER, WDir_Max INTEGER, WDir_Avg REAL, WGst_Min REAL, WGst_Max REAL, WGst_Avg REAL, SunD_Ttl INTEGER, Rain_Ttl REAL, MSLP_Min REAL, MSLP_Max REAL, MSLP_Avg REAL, ST10_Min REAL, ST10_Max REAL, ST10_Avg REAL, ST30_Min REAL, ST30_Max REAL, ST30_Avg REAL, ST00_Min REAL, ST00_Max REAL, ST00_Avg REAL)"

SELECT_SINGLE_UTCREPORTS = "SELECT * FROM utcReports WHERE Time = ?"
SELECT_SINGLE_UTCENVIRON = "SELECT * FROM utcEnviron WHERE Time = ?"
SELECT_SINGLE_LOCALSTATS = "SELECT * FROM localStats WHERE Date = ?"

GENERATE_STATS_UTCREPORTS = "SELECT min(AirT), max(AirT), ROUND(avg(AirT), 3), min(RelH), max(RelH), ROUND(avg(RelH), 3), min(DewP), max(DewP), ROUND(avg(DewP), 3), min(WSpd), max(WSpd), ROUND(avg(WSpd), 3), min(WDir), max(WDir), ROUND(avg(WDir), 3), min(WGst), max(WGst), ROUND(avg(WGst), 3), sum(SunD), sum(Rain), min(MSLP), max(MSLP), ROUND(avg(MSLP), 3), min(ST10), max(ST10), ROUND(avg(ST10), 3), min(ST30), max(ST30), ROUND(avg(ST30), 3), min(ST00), max(ST00), ROUND(avg(ST00), 3) FROM utcReports WHERE Time BETWEEN ? AND ?"
GENERATE_STATS_UTCENVIRON = "SELECT min(EncT), max(EncT), avg(EncT), min(CPUT), max(CPUT), avg(CPUT) FROM utcEnviron WHERE Time BETWEEN ? AND ?"
GENERATE_STATS_LOCALSTATS = "SELECT min(AirT_Min), max(AirT_Max), avg(AirT_Avg), min(RelH_Min), max(RelH_Max), avg(RelH_Avg), min(DewP_Min), max(DewP_Max), avg(DewP_Avg), min(WSpd_Min), max(WSpd_Max), avg(WSpd_Avg), min(WDir_Min), max(WDir_Max), avg(WDir_Avg), min(WGst_Min), max(WGst_Max), avg(WGst_Avg), sum(SunD_Ttl), sum(Rain_Ttl), min(MSLP_Min), max(MSLP_Max), avg(MSLP_Avg), min(ST10_Min), max(ST10_Max), avg(ST10_Avg), min(ST30_Min), max(ST30_Max), avg(ST30_Avg), min(ST00_Min), max(ST00_Max), avg(ST00_Avg) FROM localStats WHERE Date BETWEEN ? AND ?"

INSERT_SINGLE_UTCREPORTS = "INSERT INTO utcReports VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
INSERT_SINGLE_UTCENVIRON = "INSERT INTO utcEnviron VALUES (?, ?, ?)"
INSERT_SINGLE_LOCALSTATS = "INSERT INTO localStats (Date, AirT_Min, AirT_Max, AirT_Avg, RelH_Min, RelH_Max, RelH_Avg, DewP_Min, DewP_Max, DewP_Avg, WSpd_Min, WSpd_Max, WSpd_Avg, WDir_Min, WDir_Max, WDir_Avg, WGst_Min, WGst_Max, WGst_Avg, SunD_Ttl, Rain_Ttl, MSLP_Min, MSLP_Max, MSLP_Avg, ST10_Min, ST10_Max, ST10_Avg, ST30_Min, ST30_Max, ST30_Avg, ST00_Min, ST00_Max, ST00_Avg) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"

UPDATE_SINGLE_LOCALSTATS = "UPDATE localStats SET AirT_Min = ?, AirT_Max = ?, AirT_Avg = ?, RelH_Min = ?, RelH_Max = ?, RelH_Avg = ?, DewP_Min = ?, DewP_Max = ?, DewP_Avg = ?, WSpd_Min = ?, WSpd_Max = ?, WSpd_Avg = ?, WDir_Min = ?, WDir_Max = ?, WDir_Avg = ?, WGst_Min = ?, WGst_Max = ?, WGst_Avg = ?, SunD_Ttl = ?, Rain_Ttl = ?, MSLP_Min = ?, MSLP_Max = ?, MSLP_Avg = ?, ST10_Min = ?, ST10_Max = ?, ST10_Avg = ?, ST30_Min = ?, ST30_Max = ?, ST30_Avg = ?, ST00_Min = ?, ST00_Max = ?, ST00_Avg = ? WHERE Date = ?"
