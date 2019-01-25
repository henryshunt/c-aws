The aim of the C-AWS project was to develop, from scratch, an automatic weather station (AWS) system with a range of sensors and insightful data visualisation, using non-professional sensors and electronics, that was somewhat comparable to existing commercial AWS systems. This repository contains the software for the weather station unit itself, a Raspberry Pi running Linux Stretch Lite. It is written in Python and is into its 5th major version.

# Breakdown
The C-AWS software is split into three subsystems: `data`, `support`, and `access`. Each one manages its own distinct subset of operations:
- `data` is responsible for logging sensor data and generating statistics. All database writes happens here
- `support` is responsible for providing supporting functionality (such as uploading data to a remote server, and providing hardware power controls)
- `access` is responsible for sustaining a web server on the local network, that allows the data to be viewed

The entry point for the software is `main.py`. It performs initialisation and system checks before starting the subsystems.

# Usage
- Run `SETUP.sh` with sudo privileges to download and install all required dependencies.
- Open the file `/etc/rc.local` and add two new lines before the `exit 0` line. These automatically start the software when the system boots:
    - `cd <path to c-aws directory>`
    - `sudo python3 main.py`
- Modify `config.ini` to configure the operation of the weather station (see below)

# Configuration
The operation of the C-AWS system can be modified by editing the `config.ini` file. Subsystems and individual sensors can be turned off, and location and remote server information can be specified.

|Option|Description|
|--|--|
|`Location`|The "name" of the station, intended to be used to describe its location|
|`TimeZone`|Specifies the local time zone of the station. Must be a valid name in the IANA time zone database (e.g. `Europe/London`)|
|`Latitude`|The latitude of the station, in decimal degrees|
|`Longitude`|The longitude of the station, in decimal degrees|
|`Elevation`|The elevation of the station above sea level, in metres|
|`DataDirectory`|Absolute path to the directory that should be used to store the database of logged data|
|`CameraDrive`|The name of the removable storage drive that will be used to store images taken by the camera. The drive must have the same name|
|`RemoteSQLServer`|URL of the file that will be used to upload data to a remote server (e.g. `https://www.myserver.com/weather/add_data.php`). Must be able to receive the data via POST
|`RemoteFTPServer`|URL of the FTP server that will be used to upload camera images to (e.g. `ftp.myserver.com`)|
|`RemoteFTPUsername`|Username of the FTP server account to upload camera images to. Ensure the account directory is correctly set, files will upload directly to it|
|`RemoteFTPPassword`|Password of the above FTP user|
|`EnvReportLogging`|Should the system log environmental data to the database (such as CPU and enclosure temperatures)?|
|`CameraLogging`|Should the system log images from the camera?|
|`DayStatGeneration`|Should the system save statistics (averages, minimums, maximums, etc.) to the database for each day in the local time zone?|
|`ReportUploading`|Should the system upload data reports to the remote SQL server?|
|`EnvReportUploading`|Should the system upload environment data reports to the remote SQL server?|
|`DayStatUploading`|Should the system upload the daily statistics to the remote SQL database?|
|`CameraUploading`|Should the system upload camera images to the remote FTP server?|
|`LocalServer`|Should the system sustain a server on the local network? This can be used to view the data without requiring internet and remote server uploading
|`LogAirT`| Should the system log data from the air temperature sensor? This sensor should be inside a radiation shield
|`AirTAddress`|The address of the DS18B20 probe (e.g. `28-04167053d6ff`) to use for air temperature measurements
|`LogExpT`| Should the system log data from the exposed temperature sensor? This is not a conventional AWS parameter but it provides an interesting indicator of conditions. This sensor should not be inside a radiation shield
|`ExpTAddress`|The address of the DS18B20 probe (e.g. `28-04167053d6ff`) to use for exposed temperature measurements
|`LogRelH`|Should the system log data from the relative humidity sensor?|
|`LogDewP`|Should the system calculate and log dew point?|
|`LogWSpd`|Should the system log data from the wind speed sensor?|
|`LogWDir`|Should the system log data from the wind direction sensor?|
|`LogWGst`|Should the system calculate and log wind gust?|
|`LogSunD`|Should the system log data from the sunshine duration sensor?|
|`LogRain`|Should the system log data from the rainfall sensor?|
|`LogStaP`|Should the system log data from the barometric pressure sensor (pressure at station elevation)?|
|`LogMSLP`|Should the system calculate and log mean sea level pressure?|
|`LogST10`| Should the system log data from the soil temperature sensor at 10CM down?
|`ST10Address`|The address of the DS18B20 probe (e.g. `28-04167053d6ff`) to use for soil temperature measurements at 10CM down
|`LogST30`| Should the system log data from the soil temperature sensor at 30CM down?
|`ST30Address`|The address of the DS18B20 probe (e.g. `28-04167053d6ff`) to use for soil temperature measurements at 30CM down
|`LogST00`| Should the system log data from the soil temperature sensor at 1M down?
|`ST00Address`|The address of the DS18B20 probe (e.g. `28-04167053d6ff`) to use for soil temperature measurements at 1M down.
|`LogEncT`| Should the system log data from the enclosure temperature sensor? This sensor should be inside the C-AWS electronics box?
|`EncTAddress`|The address of the DS18B20 probe (e.g. `28-04167053d6ff`) to use for enclosure temperature measurements
|`LogCPUT`|Should the system log data from the computer's CPU temperature sensor?|

# Error Codes
A set of error codes is provided to indicate failures during initialisation and startup of the software. These codes are conveyed by continuously flashing the error LED a number of times to indicate the number of the error code, with each set of flashes separated by a longer pause. These error codes are described below.

A situation where both the data and error LEDs illuminate for 2.5 seconds, go off, and then come back on momentarily indicates a successful startup of the software.

|Flashes|Description|
|--|--|
|`1`|The configuration file contains an invalid or bad configuration|
|`2`|Not enough free space (< 1GB) remains on the internal drive (or an error occurred while getting the free space)|
|`3`|An error occurred while creating the `DataDirectory`|
|`4`|An error occurred while creating a new database file in the `DataDirectory`|
|`5`|The specified `CameraDrive` is not connected to the system|
|`6`|An error occurred while trying to mount the `CameraDrive`|
|`7`|Not enough free space (< 5GB) remains on the `CameraDrive` (or an error occurred while getting the free space)|
|`8`|Camera not connected (or an error occurred while trying to connect to it)|
|`9`|An error occurred while trying to launch the access subsystem|
|`10`|An error occurred while trying to launch the support subsystem|
|`11`|An error occurred while trying to launch the data subsystem|