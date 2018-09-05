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
    + "AirT_Avg REAL, AirT_Min REAL, AirT_Max REAL, RelH_Avg REAL, RelH_Min REAL, RelH_Max REAL, "
    + "DewP_Avg REAL, DewP_Min REAL, DewP_Max REAL, WSpd_Avg REAL, WSpd_Min REAL, WSpd_Max REAL, "
    + "WDir_Avg INTEGER, WDir_Min INTEGER, WDir_Max INTEGER, "
    + "WGst_Avg REAL, WGst_Min REAL, WGst_Max REAL, "
    + "SunD_Ttl INTEGER, Rain_Ttl REAL, "
    + "MSLP_Avg REAL, MSLP_Min REAL, MSLP_Max REAL, ST10_Avg REAL, ST10_Min REAL, ST10_Max REAL, "
    + "ST30_Avg REAL, ST30_Min REAL, ST30_Max REAL, ST00_Avg REAL, ST00_Min REAL, ST00_Max REAL"
    + ")")

SELECT_SINGLE_REPORT = "SELECT * FROM reports WHERE Time = ?"
SELECT_SINGLE_ENVREPORT = "SELECT * FROM envReports WHERE Time = ?"
SELECT_SINGLE_DAYSTAT = "SELECT * FROM dayStats WHERE Date = ?"

SELECT_RANGE_REPORTS = "SELECT * FROM reports WHERE Time BETWEEN ? AND ?"
SELECT_PAST_HOUR_REPORTS = "SELECT SUM({0}) AS {0}_PHr FROM reports WHERE Time BETWEEN ? AND ?"
SELECT_RANGE_ENVREPORTS = "SELECT * FROM envReports WHERE Time BETWEEN ? AND ?"
SELECT_RANGE_DAYSTATS = "SELECT * FROM dayStats WHERE Date BETWEEN ? AND ?"

SELECT_FIELDS_REPORTS = "SELECT {} FROM reports WHERE Time BETWEEN ? AND ?"
SELECT_FIELDS_ENVREPORTS = "SELECT {} FROM envReports WHERE Time BETWEEN ? AND ?"
SELECT_FIELDS_DAYSTATS = "SELECT {} FROM dayStats WHERE Date BETWEEN ? AND ?"

GENERATE_DAYSTAT = ("SELECT "
    + "ROUND(AVG(AirT), 3) AS AirT_Avg, MIN(AirT) AS AirT_Min, MAX(AirT) AS AirT_Max, "
    + "ROUND(AVG(RelH), 3) AS RelH_Avg, MIN(RelH) AS RelH_Min, MAX(RelH) AS RelH_Max, "
    + "ROUND(AVG(DewP), 3) AS DewP_Avg, MIN(DewP) AS DewP_Min, MAX(DewP) AS DewP_Max, "
    + "ROUND(AVG(WSpd), 3) AS WSpd_Avg, MIN(WSpd) AS WSpd_Min, MAX(WSpd) AS WSpd_Max, "
    + "ROUND(AVG(WDir), 3) AS WDir_Avg, MIN(WDir) AS WDir_Min, MAX(WDir) AS WDir_Max, "
    + "ROUND(AVG(WGst), 3) AS WGst_Avg, MIN(WGst) AS WGst_Min, MAX(WGst) AS WGst_Max, "
    + "SUM(SunD) AS SunD_Ttl, ROUND(SUM(Rain), 3) AS Rain_Ttl, "
    + "ROUND(AVG(MSLP), 3) AS MSLP_Avg, MIN(MSLP) AS MSLP_Min, MAX(MSLP) AS MSLP_Max, "
    + "ROUND(AVG(ST10), 3) AS ST10_Avg, MIN(ST10) AS ST10_Min, MAX(ST10) AS ST10_Max, "
    + "ROUND(AVG(ST30), 3) AS ST30_Avg, MIN(ST30) AS ST30_Min, MAX(ST30) AS ST30_Max, "
    + "ROUND(AVG(ST00), 3) AS ST00_Avg, MIN(ST00) AS ST00_Min, MAX(ST00) AS ST00_Max "
    + "FROM reports WHERE Time BETWEEN ? AND ?")

GENERATE_YEAR_STATS = ("SELECT "
    + "ROUND(AVG(AirT_Avg), 3) AS AirT_Avg, ROUND(MIN(AirT_Min), 3) AS AirT_Min, "
    + "ROUND(MAX(AirT_Max), 3) AS AirT_Max, ROUND(SUM(SunD_Ttl) / 60.0 / 60.0, 3) AS SunD_Ttl, "
    + "ROUND(SUM(Rain_Ttl), 3) AS Rain_Ttl FROM dayStats WHERE strftime('%Y', Date) = ?")
GENERATE_MONTHS_STATS = ("SELECT strftime('%m', Date) AS Month, "
    + "ROUND(AVG(AirT_Avg), 3) AS AirT_Avg, ROUND(MIN(AirT_Min), 3) AS AirT_Min, "
    + "ROUND(MAX(AirT_Max), 3) AS AirT_Max, ROUND(AVG(RelH_Avg), 3) AS RelH_Avg, "
    + "ROUND(AVG(WSpd_Avg), 3) AS WSpd_Avg, ROUND(MAX(WSpd_Max), 3) AS WSpd_Max, "
    + "ROUND(AVG(WDir_Avg), 3) AS WDir_Avg, ROUND(AVG(WGst_Avg), 3) AS WGst_Avg, "
    + "ROUND(MAX(WGst_Max), 3) AS WGst_Max, ROUND(SUM(SunD_Ttl) / 60.0 / 60.0, 3) AS SunD_Ttl, "
    + "ROUND(SUM(Rain_Ttl), 3) AS Rain_Ttl, ROUND(AVG(MSLP_Avg), 3) AS MSLP_Avg, "
    + "ROUND(AVG(ST10_Avg), 3) AS ST10_Avg, ROUND(AVG(ST30_Avg), 3) AS ST30_Avg, "
    + "ROUND(AVG(ST00_Avg), 3) AS ST00_Avg FROM dayStats WHERE strftime('%Y', Date) "
    + "= ? GROUP BY strftime('%m', Date)")

INSERT_REPORT = "INSERT INTO reports VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
INSERT_ENVREPORT = "INSERT INTO envReports VALUES (?, ?, ?)"
INSERT_DAYSTAT = ("INSERT INTO dayStats ("
    + "Date, AirT_Avg, AirT_Min, AirT_Max, RelH_Avg, RelH_Min, RelH_Max, DewP_Avg, DewP_Min, "
    + "DewP_Max, WSpd_Avg, WSpd_Min, WSpd_Max, WDir_Avg, WDir_Min, WDir_Max, WGst_Avg, WGst_Min, "
    + "WGst_Max, SunD_Ttl, Rain_Ttl, MSLP_Avg, MSLP_Min, MSLP_Max, ST10_Avg, ST10_Min, ST10_Max, "
    + "ST30_Avg, ST30_Min, ST30_Max, ST00_Avg, ST00_Min, ST00_Max) VALUES (?, ?, ?, ?, ?, ?, "
    + "?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)")

UPDATE_DAYSTAT = ("UPDATE dayStats SET "
    + "AirT_Avg = ?, AirT_Min = ?, AirT_Max = ?, RelH_Avg = ?, RelH_Min = ?, RelH_Max = ?, "
    + "DewP_Avg = ?, DewP_Min = ?, DewP_Max = ?, WSpd_Avg = ?, WSpd_Min = ?, WSpd_Max = ?, "
    + "WDir_Avg = ?, WDir_Min = ?, WDir_Max = ?, WGst_Avg = ?, WGst_Min = ?, WGst_Max = ?, "
    + "SunD_Ttl = ?, Rain_Ttl = ?, MSLP_Avg = ?, MSLP_Min = ?, MSLP_Max = ?, "
    + "ST10_Avg = ?, ST10_Min = ?, ST10_Max = ?, ST30_Avg = ?, ST30_Min = ?, ST30_Max = ?, "
    + "ST00_Avg = ?, ST00_Min = ?, ST00_Max = ? WHERE Date = ?")
