The aim of C-AWS was to develop from scratch a capable automatic weather station (AWS) using non-professional sensors and electronics. This repository contains the core software system, designed to run on a Raspberry Pi. See [C-AWS Server](https://github.com/henryshunt/c-aws-server) for a system to view the data.

# Breakdown
The C-AWS software is split into a `data` subsystem, which logs sensor data and generates statistics, and a `support` subsystem, which provides all other supporting functionality (such as data uploading and power controls). There was previously also an `access` subsystem which provided access to the data via a web server, but this was split out into the C-AWS Server repository.

Data is saved to an SQLite3 database, and if camera logging is enabled then the images are saved to a USB drive. Any errors that occur during initialisation or while the `data` subsystem is running will be written to an `error_log.txt` file in the specified `DataDirectory`.

`main.py` is the entry point for the software system. It performs initialisation and system checks before starting the subsystems as background processes. The rest of the code comprises a set of routines to support the codebase, as well as a set of classes that abstract each sensor behind a common interface.

# Usage
Supported sensors: DS18B20 (temperature), SHT31-D (humidity), Inspeed Classic Anemometer (wind speed), Inspeed E-Vane II (wind direction), Instromet Mini Sun Board with binary output (sunshine duration), Rainwise Rainew 111 (rainfall), BME280 (pressure), Raspberry Pi Camera Module (camera).

- Run `SETUP.sh` with `sudo` privileges to download and install the required dependencies
- Set the system time zone to UTC
- If logging from a camera, create a mount directory for a USB drive to store the images
- Edit the file `/etc/rc.local` (things to do at boot) and before the `exit 0` line:
    - If logging from a camera, mount the drive to the mount directory
    - Add `cd <path to c-aws directory>`
    - Add `sudo python3 main.py`
- Configure the operation of the C-AWS software (see the configuration section below)
- Restart the computer to run the software

# Configuration
Use `config.ini` to supply station information, data save locations, data upload endpoints, operation configuration, and sensor configuration. Various option values can be omitted if they have nothing that depends on them (e.g. you don't need to provide a `CameraDirectory` value if `CameraLogging` is not enabled).

|Option|Description|
|--|--|
|`TimeZone`|Required. Local time zone of the station. Must be a valid name in the IANA time zone database (e.g. `Europe/London`)|
|`Latitude`|Required. Latitude of the station in decimal degrees|
|`Longitude`|Required. Longitude of the station in decimal degrees|
|`Elevation`|Required. Elevation of the station above sea level in metres|
|`DataDirectory`|Required. Absolute path to the directory that should be used to store the database of logged data|
|`CameraDirectory`|Absolute path to the directory where a USB drive, to use for storing images taken by the camera, is set to mount to|
|`RemoteSQLServer`|URL of the file that will be used to receive data on a remote server (e.g. `https://www.myserver.com/routines/add-data.php`). Designed to work with [C-AWS Server](https://github.com/henryshunt/c-aws-server)
|`RemoteFTPServer`|URL of the FTP server that will be used to upload camera images to (e.g. `ftp.myserver.com`)|
|`RemoteFTPUsername`|Username of the FTP server account to upload camera images to. Files will upload directly to the account's default directory|
|`RemoteFTPPassword`|Password of the above FTP user|
|`EnvReportLogging`|Should the system log environmental data to the database (e.g. CPU and enclosure temperatures)?|
|`CameraLogging`|Should the system log images from the camera?|
|`DayStatGeneration`|Should the system save statistics (averages, minimums, maximums, totals) to the database for each day in the local time zone?|
|`ReportUploading`|Should the system upload data reports to the remote SQL server?|
|`EnvReportUploading`|Should the system upload environment data reports to the remote SQL server?|
|`DayStatUploading`|Should the system upload the daily statistics to the remote SQL database?|
|`CameraUploading`|Should the system upload camera images to the remote FTP server?|
|`AirT`|Is a sensor connected for measuring air temperature? This sensor should be inside a radiation shield
|`AirTAddress`|The address of the DS18B20 probe (e.g. `28-04167053d6ff`) to measure the `AirT` parameter
|`ExpT`|Is a sensor connected for measuring exposed temperature? This is not a conventional parameter but it provides an interesting indicator of the general weather conditions. This sensor should not be inside a radiation shield
|`ExpTAddress`|The address of the DS18B20 probe (e.g. `28-04167053d6ff`) to measure the `ExpT` parameter
|`RelH`|Is a sensor connected for measuring relative humidity?|
|`WSpd`|Is a sensor connected for measuring wind speed?|
|`WSpdPin`|The pin number that the `WSpd` sensor is connected to|
|`WDir`|Is a sensor connected for measuring wind direction?|
|`WDirChannel`|The ADC channel number that the `WDir` sensor is connected to|
|`SunD`|Is a sensor connected for measuring sunshine duration?|
|`SunDPin`|The pin number that the `SunD` sensor is connected to|
|`Rain`|Is a sensor connected for measuring rainfall?|
|`RainPin`|The pin number that the `Rain` sensor is connected to|
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
A set of error codes indicates a failure during initialisation and startup of the software. These codes are conveyed by continuously flashing the error LED a number of times to indicate the number of the error code, with each set of flashes separated by a longer pause. The error codes are listed below.

A situation where both the data and error LEDs illuminate for 2.5 seconds, go off, and then come back on momentarily indicates a successful startup of the software. However, after this, a 10-flash error code indicates that the data subsystem encountered an error while initialising one of the sensors that are marked in the configuration file as being connected.

|Flashes|Description|
|--|--|
|1|The configuration file contains an invalid or bad configuration description|
|2|Not enough free space (< 1GB) remains on the internal drive (or error getting space)|
|3|An error occurred while creating the `DataDirectory`|
|4|An error occurred while creating a new database file in the `DataDirectory`|
|5|The specified `CameraDirectory` does not exist|
|6|The specified `CameraDirectory` does not have a USB drive mounted|
|7|Not enough free space (< 5GB) remains on the `CameraDirectory` drive (or error getting space)|
|8|An error occurred while trying to launch the support subsystem|
|9|An error occurred while trying to launch the data subsystem|

# Version History
- 5.0.0 (Sep 2018): Version 5, the final major software re-write.
- 5.0.1 (Sep 2018): Fixed a bug that prevented sunshine data from being read during the last second of the minute.
- 5.0.2 (Dec 2018): Various minor tweaks to text on the data viewing pages. Removed yearly total rainfall and sunshine from climate page.
- 5.1.0 (Apr 2019): Rewritten data sub-system and various tweaks. Configuration now allows specification of which parameters to log. Fixed a bug that meant the first minute of the next day was not included in the previous day's averaged and totalled statistics. Removed monthly average wind gust from climate page. About page renamed to 'station'. Year graphs now end at the current day instead of yesterday.
- 5.1.1 (Apr 2019): Fixed a bug where the ExpT and EncT sensor addresses were the same.
- 5.1.2 (Apr 2019): Fixed a bug preventing rainfall from being counted.
- 5.2.0 (Jun 2019): Removed the access subsystem (replaced with separate codebade) and associated routines. Various small changes and fault tolerance improvements. Removed code to mount the camera drive.