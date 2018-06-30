CREATE_REPORTS_TABLE = ("CREATE TABLE reports ("
    + "Time TEXT PRIMARY KEY NOT NULL, "
    + "AirT REAL, ExpT REAL, RelH REAL, DewP REAL, WSpd REAL, "
    + "WDir INTEGER, WGst REAL, SunD INTEGER, "
    + "Rain REAL, StaP REAL, MSLP REAL, ST10 REAL, ST30 REAL, ST00 REAL"
    + ")")
CREATE_ENVREPORTS_TABLE = ("CREATE TABLE envReports ("
    + "Time TEXT PRIMARY KEY NOT NULL, EncT REAL, CPUT REAL"
    + ")")
CREATE_DAYSTATS_TABLE = ("CREATE TABLE dayStats ("
    + "Date TEXT PRIMARY KEY NOT NULL, "
    + "AirT_Min REAL, AirT_Max REAL, AirT_Avg REAL, RelH_Min REAL, RelH_Max REAL, RelH_Avg REAL, "
    + "DewP_Min REAL, DewP_Max REAL, DewP_Avg REAL, WSpd_Min REAL, WSpd_Max REAL, WSpd_Avg REAL, "
    + "WDir_Min INTEGER, WDir_Max INTEGER, WDir_Avg INTEGER, "
    + "WGst_Min REAL, WGst_Max REAL, WGst_Avg REAL, "
    + "SunD_Ttl INTEGER, Rain_Ttl REAL, "
    + "MSLP_Min REAL, MSLP_Max REAL, MSLP_Avg REAL, ST10_Min REAL, ST10_Max REAL, ST10_Avg REAL, "
    + "ST30_Min REAL, ST30_Max REAL, ST30_Avg REAL, ST00_Min REAL, ST00_Max REAL, ST00_Avg REAL"
    + ")")

SELECT_SINGLE_UTCREPORTS = "SELECT * FROM utcReports WHERE Time = ?"
SELECT_SINGLE_UTCENVIRON = "SELECT * FROM utcEnviron WHERE Time = ?"
SELECT_SINGLE_LOCALSTATS = "SELECT * FROM localStats WHERE Date = ?"

SELECT_RANGE_UTCREPORTS = "SELECT * FROM utcReports WHERE Time BETWEEN ? AND ?"
SELECT_PAST_HOUR_UTCREPORTS = "SELECT SUM({0}) AS {0} FROM utcReports WHERE Time BETWEEN ? AND ?"
SELECT_RANGE_UTCENVIRON = "SELECT * FROM utcEnviron WHERE Time BETWEEN ? AND ?"
SELECT_RANGE_LOCALSTATS = "SELECT * FROM localStats WHERE Date BETWEEN ? AND ?"

SELECT_FIELDS_UTCREPORTS = "SELECT {} FROM utcReports WHERE Time BETWEEN ? AND ?"
SELECT_FIELDS_UTCENVIRON = "SELECT {} FROM utcEnviron WHERE Time BETWEEN ? AND ?"
SELECT_FIELDS_LOCALSTATS = "SELECT {} FROM localStats WHERE Date BETWEEN ? AND ?"

GENERATE_STATS_UTCREPORTS = "SELECT MIN(AirT) AS AirT_Min, MAX(AirT) AS AirT_Max, ROUND(AVG(AirT), 3) AS AirT_Avg, MIN(RelH) AS RelH_Min, MAX(RelH) AS RelH_Max, ROUND(AVG(RelH), 3) AS RelH_Avg, MIN(DewP) AS DewP_Min, MAX(DewP) AS DewP_Max, ROUND(AVG(DewP), 3) AS DewP_Avg, MIN(WSpd) AS WSpd_Min, MAX(WSpd) AS WSpd_Max, ROUND(AVG(WSpd), 3) AS WSpd_Avg, MIN(WDir) AS WDir_Min, MAX(WDir) AS WDir_Max, ROUND(AVG(WDir), 3) AS WDir_Avg, MIN(WGst) AS WGst_Min, MAX(WGst) AS WGst_Max, ROUND(MAX(WGst), 3) AS WGst_Avg, SUM(SunD) AS SunD_Ttl, SUM(Rain) AS Rain_Ttl, MIN(MSLP) AS MSLP_Min, MAX(MSLP) AS MSLP_Max, ROUND(AVG(MSLP), 3) AS MSLP_Avg, MIN(ST10) AS ST10_Min, MAX(ST10) AS ST10_Max, ROUND(AVG(ST10), 3) AS ST10_Avg, MIN(ST30) AS ST30_Min, MAX(ST30) AS ST30_Max, ROUND(AVG(ST30), 3) AS ST30_Avg, MIN(ST00) AS ST00_Min, MAX(ST00) AS ST00_Max, ROUND(AVG(ST00), 3) AS ST00_Avg FROM utcReports WHERE Time BETWEEN ? AND ?"
GENERATE_STATS_UTCENVIRON = "SELECT MIN(EncT) AS EncT_Min, MAX(EncT) AS EncT_Max, ROUND(AVG(EncT), 3) AS EncT_Avg, MIN(CPUT) AS CPUT_Min, MAX(CPUT) AS CPUT_Max, ROUND(AVG(CPUT), 3) AS CPUT_Avg FROM utcEnviron WHERE Time BETWEEN ? AND ?"
GENERATE_STATS_LOCALSTATS = "SELECT MIN(AirT_Min) AS AirT_Min_Min, MAX(AirT_Max) AS AirT_Max_Max, ROUND(AVG(AirT_Avg), 3) AS AirT_Avg_Avg, MIN(RelH_Min) AS RelH_Min_Min, MAX(RelH_Max) AS RelH_Max_Max, ROUND(AVG(RelH_Avg), 3) AS RelH_Avg_Avg, MIN(DewP_Min) AS DewP_Min_Min, MAX(DewP_Max) AS DewP_Max_Max, ROUND(AVG(DewP_Avg), 3) AS DewP_Avg_Avg, MIN(WSpd_Min) AS WSpd_Min_Min, MAX(WSpd_Max) AS WSpd_Max_Max, ROUND(AVG(WSpd_Avg), 3) AS WSpd_Avg_Avg, MIN(WDir_Min) AS WDir_Min_Min, MAX(WDir_Max) AS WDir_Max_Max, ROUND(AVG(WDir_Avg), 3) AS WDir_Avg_Avg, MIN(WGst_Min) AS WGst_Min_Min, MAX(WGst_Max) AS WGst_Max_Max, ROUND(AVG(WGst_Avg), 3) AS WGst_Avg_Avg, SUM(SunD_Ttl) AS SunD_Ttl_Ttl, SUM(Rain_Ttl) AS Rain_Ttl_Ttl, MIN(MSLP_Min) AS MSLP_Min_Min, MAX(MSLP_Max) AS MSLP_Max_Max, ROUND(AVG(MSLP_Avg), 3) AS MSLP_Avg_Avg, MIN(ST10_Min) AS ST10_Min_Min, MAX(ST10_Max) AS ST10_Max_Max, ROUND(AVG(ST10_Avg), 3) AS ST10_Avg_Avg, MIN(ST30_Min) AS ST30_Min_Min, MAX(ST30_Max) AS ST30_Max_Max, ROUND(AVG(ST30_Avg), 3) AS ST30_Avg_Avg, MIN(ST00_Min) AS ST00_Min_Min, MAX(ST00_Max) AS ST00_Max_Max, ROUND(AVG(ST00_Avg), 3) AS ST00_Avg_Avg FROM localStats WHERE Date BETWEEN ? AND ?"

INSERT_SINGLE_UTCREPORTS = "INSERT INTO utcReports VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
INSERT_SINGLE_UTCENVIRON = "INSERT INTO utcEnviron VALUES (?, ?, ?)"
INSERT_SINGLE_LOCALSTATS = "INSERT INTO localStats (Date, AirT_Min, AirT_Max, AirT_Avg, RelH_Min, RelH_Max, RelH_Avg, DewP_Min, DewP_Max, DewP_Avg, WSpd_Min, WSpd_Max, WSpd_Avg, WDir_Min, WDir_Max, WDir_Avg, WGst_Min, WGst_Max, WGst_Avg, SunD_Ttl, Rain_Ttl, MSLP_Min, MSLP_Max, MSLP_Avg, ST10_Min, ST10_Max, ST10_Avg, ST30_Min, ST30_Max, ST30_Avg, ST00_Min, ST00_Max, ST00_Avg) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"

UPDATE_SINGLE_LOCALSTATS = "UPDATE localStats SET AirT_Min = ?, AirT_Max = ?, AirT_Avg = ?, RelH_Min = ?, RelH_Max = ?, RelH_Avg = ?, DewP_Min = ?, DewP_Max = ?, DewP_Avg = ?, WSpd_Min = ?, WSpd_Max = ?, WSpd_Avg = ?, WDir_Min = ?, WDir_Max = ?, WDir_Avg = ?, WGst_Min = ?, WGst_Max = ?, WGst_Avg = ?, SunD_Ttl = ?, Rain_Ttl = ?, MSLP_Min = ?, MSLP_Max = ?, MSLP_Avg = ?, ST10_Min = ?, ST10_Max = ?, ST10_Avg = ?, ST30_Min = ?, ST30_Max = ?, ST30_Avg = ?, ST00_Min = ?, ST00_Max = ?, ST00_Avg = ? WHERE Date = ?"
