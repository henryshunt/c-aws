#!/bin/bash
echo "Installing dependencies for C-AWS..."

apt-get install python3-rpi.gpio
apt-get install python3-picamera
apt-get install python3-tz
apt-get install python3-gpiozero
apt-get install python3-apscheduler
apt-get install python-spidev

apt-get install python3-pip
pip3 install adafruit-blinka
pip3 install Adafruit_GPIO
pip3 install astral
pip3 install python-daemon
pip3 install adafruit-circuitpython-mcp9808
pip3 install adafruit-circuitpython-htu21d
pip3 install adafruit-circuitpython-bme280
pip3 install adafruit-circuitpython-mcp3xxx

echo "DONE installing dependencies for C-AWS"