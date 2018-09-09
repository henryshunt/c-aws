# C-AWS
The aim of this project was to develop, from scratch, an automatic weather station with a wide range of sensors and in-depth data visualisation, using cheaper non- and semi-professional sensors and data logging equipment, that was comparable to existing commercial systems. This repository contains the code for the weather station unit itself, and is designed to run on Linux Stretch Lite on a Raspberry Pi.

# Dependencies
These dependencies are relative to a fresh install of Raspbian Stretch Lite.

- `RPi.GPIO` -- `sudo apt-get install python3-rpi.gpio`
- `picamera` -- `sudo apt-get install python3-picamera`
- `pytz` -- `sudo apt-get install python3-tz`
- `gpiozero` -- `sudo apt-get install python3-gpiozero`
- `apscheduler` -- `sudo apt-get install python3-apscheduler`
- `Adafruit_GPIO` -- `sudo pip3 install Adafruit_GPIO`
- `astral` -- `sudo pip3 install astral`
- `flask` -- `sudo pip3 install flask`
- `python-daemon` -- `sudo pip3 install python-daemon`
- `spidev` -- `sudo apt-get install python-spidev`
