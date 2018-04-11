CREATE_UTCREPORTS_TABLE = "CREATE TABLE utcReports (Time TEXT PRIMARY KEY NOT NULL, AirT REAL, ExpT REAL, RelH REAL, DewP REAL, WSpd REAL, WDir INTEGER, WGst REAL, SunD INTEGER, Rain REAL, StaP REAL, PTen REAL, MSLP REAL, ST10 REAL, ST30 REAL, ST00 REAL)"
CREATE_UTCENVIRON_TABLE = "CREATE TABLE utcEnviron (Time TEXT PRIMARY KEY NOT NULL, EncT REAL, CPUT REAL)"
CREATE_LOCALSTATS_TABLE = "CREATE TABLE localStats (Date TEXT PRIMARY KEY NOT NULL, AirT_Min REAL, AirT_Max REAL, AirT_Avg REAL, RelH_Min REAL, RelH_Max REAL, RelH_Avg REAL, DewP_Min REAL, DewP_Max REAL, DewP_Avg REAL, WSpd_Min REAL, WSpd_Max REAL, WSpd_Avg REAL, WDir_Min INTEGER, WDir_Max INTEGER, WDir_Avg REAL, WGst_Min REAL, WGst_Max REAL, WGst_Avg REAL, SunD_Ttl INTEGER, Rain_Ttl REAL, MSLP_Min REAL, MSLP_Max REAL, MSLP_Avg REAL, ST10_Min REAL, ST10_Max REAL, ST10_Avg REAL, ST30_Min REAL, ST30_Max REAL, ST30_Avg REAL, ST00_Min REAL, ST00_Max REAL, ST00_Avg REAL)"

SELECT_SINGLE_UTCREPORTS = "SELECT * FROM utcReports WHERE Time = ?"
SELECT_SINGLE_UTCENVIRON = "SELECT * FROM utcEnviron WHERE Time = ?"
SELECT_SINGLE_LOCALSTATS = "SELECT * FROM localStats WHERE Date = ?"

SELECT_RANGE_UTCREPORTS = "SELECT * FROM utcReports WHERE Time BETWEEN ? AND ?"
SELECT_RANGE_UTCENVIRON = "SELECT * FROM utcEnviron WHERE Time BETWEEN ? AND ?"
SELECT_RANGE_LOCALSTATS = "SELECT * FROM localStats WHERE Date BETWEEN ? AND ?"

GENERATE_STATS_UTCREPORTS = "SELECT MIN(AirT), MAX(AirT), ROUND(AVG(AirT), 3), MIN(RelH), MAX(RelH), ROUND(AVG(RelH), 3), MIN(DewP), MAX(DewP), ROUND(AVG(DewP), 3), MIN(WSpd), MAX(WSpd), ROUND(AVG(WSpd), 3), MIN(WDir), MAX(WDir), ROUND(AVG(WDir), 3), MIN(WGst), MAX(WGst), ROUND(MAX(WGst), 3), SUM(SunD), SUM(Rain), MIN(MSLP), MAX(MSLP), ROUND(AVG(MSLP), 3), MIN(ST10), MAX(ST10), ROUND(AVG(ST10), 3), MIN(ST30), MAX(ST30), ROUND(AVG(ST30), 3), MIN(ST00), MAX(ST00), ROUND(AVG(ST00), 3) FROM utcReports WHERE Time BETWEEN ? AND ?"
GENERATE_STATS_UTCENVIRON = "SELECT MIN(EncT), MAX(EncT), ROUND(AVG(EncT), 3), MIN(CPUT), MAX(CPUT), ROUND(AVG(CPUT), 3) FROM utcEnviron WHERE Time BETWEEN ? AND ?"
GENERATE_STATS_LOCALSTATS = "SELECT MIN(AirT_Min), MAX(AirT_Max), ROUND(AVG(AirT_Avg), 3), MIN(RelH_Min), MAX(RelH_Max), ROUND(AVG(RelH_Avg), 3), MIN(DewP_Min), MAX(DewP_Max), ROUND(AVG(DewP_Avg), 3), MIN(WSpd_Min), MAX(WSpd_Max), ROUND(AVG(WSpd_Avg), 3), MIN(WDir_Min), MAX(WDir_Max), ROUND(AVG(WDir_Avg), 3), MIN(WGst_Min), MAX(WGst_Max), ROUND(AVG(WGst_Avg), 3), SUM(SunD_Ttl), SUM(Rain_Ttl), MIN(MSLP_Min), MAX(MSLP_Max), ROUND(AVG(MSLP_Avg), 3), MIN(ST10_Min), MAX(ST10_Max), ROUND(AVG(ST10_Avg), 3), MIN(ST30_Min), MAX(ST30_Max), ROUND(AVG(ST30_Avg), 3), MIN(ST00_Min), MAX(ST00_Max), ROUND(AVG(ST00_Avg), 3) FROM localStats WHERE Date BETWEEN ? AND ?"

INSERT_SINGLE_UTCREPORTS = "INSERT INTO utcReports VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
INSERT_SINGLE_UTCENVIRON = "INSERT INTO utcEnviron VALUES (?, ?, ?)"
INSERT_SINGLE_LOCALSTATS = "INSERT INTO localStats (Date, AirT_Min, AirT_Max, AirT_Avg, RelH_Min, RelH_Max, RelH_Avg, DewP_Min, DewP_Max, DewP_Avg, WSpd_Min, WSpd_Max, WSpd_Avg, WDir_Min, WDir_Max, WDir_Avg, WGst_Min, WGst_Max, WGst_Avg, SunD_Ttl, Rain_Ttl, MSLP_Min, MSLP_Max, MSLP_Avg, ST10_Min, ST10_Max, ST10_Avg, ST30_Min, ST30_Max, ST30_Avg, ST00_Min, ST00_Max, ST00_Avg) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"

UPDATE_SINGLE_LOCALSTATS = "UPDATE localStats SET AirT_Min = ?, AirT_Max = ?, AirT_Avg = ?, RelH_Min = ?, RelH_Max = ?, RelH_Avg = ?, DewP_Min = ?, DewP_Max = ?, DewP_Avg = ?, WSpd_Min = ?, WSpd_Max = ?, WSpd_Avg = ?, WDir_Min = ?, WDir_Max = ?, WDir_Avg = ?, WGst_Min = ?, WGst_Max = ?, WGst_Avg = ?, SunD_Ttl = ?, Rain_Ttl = ?, MSLP_Min = ?, MSLP_Max = ?, MSLP_Avg = ?, ST10_Min = ?, ST10_Max = ?, ST10_Avg = ?, ST30_Min = ?, ST30_Max = ?, ST30_Avg = ?, ST00_Min = ?, ST00_Max = ?, ST00_Avg = ? WHERE Date = ?"
