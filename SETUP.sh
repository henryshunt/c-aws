#!/bin/bash
echo "Installing dependencies for C-AWS..."

apt-get update
apt-get upgrade

apt-get install python3-rpi.gpio
apt-get install python3-picamera
apt-get install python3-tz
apt-get install python3-gpiozero
apt-get install python3-apscheduler
apt-get install python-spidev

apt-get install python3-pip

pip3 install Adafruit_GPIO
pip3 install astral
pip3 install python-daemon

echo "DONE installing dependencies for C-AWS"