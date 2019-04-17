The aim of the C-AWS project was to develop, from scratch, an automatic weather station (AWS) system with a range of sensors and insightful data visualisation, using non-professional sensors and electronics, that was somewhat comparable to existing commercial AWS systems. This repository contains the software for the weather station unit itself, a Raspberry Pi running Linux Stretch Lite. It is written in Python and is into its 5th major version.

# Breakdown
The C-AWS software is split into three subsystems: `data`, `support`, and `access`. Each one manages its own distinct subset of operations:
- `data` is responsible for logging sensor data and generating statistics. All database writes happen here.
- `support` is responsible for providing extra supporting functionality (such as uploading data to a remote server).
- `access` is responsible for enabling access to the data and system controls (power controls, etc.) on the local network.

The entry point for the software is `main.py`. It performs initialisation and system checks before starting each subsystem.

# Usage
- Run `SETUP.sh` with `sudo` privileges to download and install the required dependencies.
- Open the file `/etc/rc.local` and add two new lines before the `exit 0` line. These automatically start the software when the system boots:
    - `cd <path to c-aws directory>`
    - `sudo python3 main.py`
- Configure the operation of the C-AWS software (see the configuration section below)
- Restart the computer to run the software

# Configuration
The operation of the C-AWS software can be modified by editing the `config.ini` file. Subsystems and individual sensors can be turned off, and location and remote server information can be specified.

|Option|Description|
|--|--|
|`Location`|The "name" of the station, intended to be used to describe its location. This appears as the title and header of pages on the local network server|
|`TimeZone`|Specifies the local time zone of the station. Must be a valid name in the IANA time zone database (e.g. `Europe/London`)|
|`Latitude`|The latitude of the station in decimal degrees|
|`Longitude`|The longitude of the station in decimal degrees|
|`Elevation`|The elevation of the station above sea level in metres|
|`DataDirectory`|Absolute path to the directory that should be used to store the database of logged data|
|`CameraDrive`|The name of the removable storage drive that will be used to store images taken by the camera|
|`RemoteSQLServer`|URL of the file that will be used to upload data to a remote server (e.g. `https://www.myserver.com/weather/add_data.php`). Must be able to receive the data via POST
|`RemoteFTPServer`|URL of the FTP server that will be used to upload camera images to (e.g. `ftp.myserver.com`)|
|`RemoteFTPUsername`|Username of the FTP server account to upload camera images to. Ensure the account's directory is correctly set, files will upload directly to it|
|`RemoteFTPPassword`|Password of the above FTP user|
|`EnvReportLogging`|Should the system log environmental data to the database (e.g. CPU and enclosure temperatures)?|
|`CameraLogging`|Should the system log images from the camera?|
|`DayStatGeneration`|Should the system save statistics (averages, minimums, maximums, etc.) to the database for each day in the local time zone?|
|`ReportUploading`|Should the system upload data reports to the remote SQL server?|
|`EnvReportUploading`|Should the system upload environment data reports to the remote SQL server?|
|`DayStatUploading`|Should the system upload the daily statistics to the remote SQL database?|
|`CameraUploading`|Should the system upload camera images to the remote FTP server?|
|`LocalServer`|Should the system sustain a server on the local network? This can be used to view the data without requiring an internet connection and remote server uploading
|`AirT`|Is a sensor connected for measuring air temperature? This sensor should be inside a radiation shield
|`AirTAddress`|The address of the DS18B20 probe (e.g. `28-04167053d6ff`) to measure the `AirT` parameter
|`ExpT`|Is a sensor connected for measuring exposed temperature? This is not a conventional parameter but it provides an interesting indicator of the general weather conditions. This sensor should not be inside a radiation shield
|`ExpTAddress`|The address of the DS18B20 probe (e.g. `28-04167053d6ff`) to measure the `ExpT` parameter
|`RelH`|Is a sensor connected for measuring relative humidity?|
|`WSpd`|Is a sensor connected for measuring wind speed?|
|`WDir`|Is a sensor connected for measuring wind direction?|
|`SunD`|Is a sensor connected for measuring sunshine duration?|
|`Rain`|Is a sensor connected for measuring rainfall?|
|`StaP`|Is a sensor connected for measuring barometric pressure at station elevation?|
|`ST10`|Is a sensor connected for measuring soil temperature at 10CM down?
|`ST10Address`|The address of the DS18B20 probe (e.g. `28-04167053d6ff`) to measure the `ST10` parameter
|`ST30`|Is a sensor connected for measuring soil temperature at 30CM down?
|`ST30Address`|The address of the DS18B20 probe (e.g. `28-04167053d6ff`) to measure the `ST30` parameter
|`ST00`|Is a sensor connected for measuring soil temperature at 1M down?
|`ST00Address`|The address of the DS18B20 probe (e.g. `28-04167053d6ff`) to measure the `ST00` parameter
|`EncT`|Is a sensor connected for measuring enclosure temperature? This sensor should be inside the station's electronics box
|`EncTAddress`|The address of the DS18B20 probe (e.g. `28-04167053d6ff`) to measure the `EncT` parameter
|`LogDewP`|Should dew point be calculated and logged? This requires the `AirT` and `RelH` sensors|
|`LogWGst`|Should wind gust be calculated and logged? This requires the `WSpd` sensor|
|`LogMSLP`|Should mean sea level pressure be calculated and logged? This requires the `StaP`, `AirT` and `DewP` sensors|

# Error Codes
A set of error codes is provided to indicate failures during initialisation and startup of the software. These codes are conveyed by continuously flashing the error LED a number of times to indicate the number of the error code, with each set of flashes separated by a longer pause. These error codes are described below.

A situation where both the data and error LEDs illuminate for 2.5 seconds, go off, and then come back on momentarily indicates a successful startup of the software. However, after this, a 12-flash error code indicates that the data subsystem has encountered an error while initialising one of the sensors that are marked in the configuration file as being connected.

|Flashes|Description|
|--|--|
|`1`|The configuration file contains an invalid or bad configuration description|
|`2`|Not enough free space (< 1GB) remains on the internal drive (or an error occurred while getting the free space)|
|`3`|An error occurred while creating the `DataDirectory`|
|`4`|An error occurred while creating a new database file in the `DataDirectory`|
|`5`|The specified `CameraDrive` is not connected to the system|
|`6`|An error occurred while trying to mount the `CameraDrive`|
|`7`|Not enough free space (< 5GB) remains on the `CameraDrive` (or an error occurred while getting the free space)|
|`8`|An error occurred while trying to launch the access subsystem|
|`9`|An error occurred while trying to launch the support subsystem|
|`10`|An error occurred while trying to launch the data subsystem|

# Version History
- 5.0.0 (Sep 2018): Version 5, the final major software re-write.
- 5.0.1 (Sep 2018): Fixed a bug that prevented sunshine data from being read during the last second of the minute.
- 5.0.2 (Dec 2018): Various minor tweaks to text on the data viewing pages. Removed yearly total rainfall and sunshine from climate page.
- 5.1.0 (Apr 2019): Rewritten data sub-system and various tweaks. Configuration now allows specification of which parameters to log. Fixed a bug that meant the first minute of the next day was not included in the previous day's averaged and totalled statistics. Removed monthly average wind gust from climate page.