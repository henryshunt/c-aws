#!/bin/bash
echo "Installing C-AWS software dependencies..."

apt-get install python3-rpi.gpio
apt-get install python3-apscheduler
apt-get install python3-tz
apt-get install python3-gpiozero
apt-get install python3-picamera

apt-get install python3-pip
pip3 install python-daemon
pip3 install adafruit-blinka
pip3 install adafruit-circuitpython-mcp9808
pip3 install adafruit-circuitpython-htu21d
pip3 install adafruit-circuitpython-bme280
pip3 install adafruit-circuitpython-mcp3xxx
pip3 install astral
pip3 install watchdog

echo "Finished installing C-AWS software dependencies"