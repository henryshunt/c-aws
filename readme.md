The aim of the C-AWS project was to develop, from scratch, an automatic weather station (AWS) system with a range of sensors as well as data visualisation, using cheaper non- and semi-professional sensors and data logging equipment, that was comparable to existing commercial AWS systems. This repository contains the code for the weather station unit itself, a Raspberry Pi running Linux Stretch Lite.

# Usage
- Run `setup.sh` with sudo privileges to download and install all required dependencies.
- Open the file `/etc/rc.local` and add two new lines before the `exit 0` line. These automatically start the software when the system boots:
    - `cd <path to c-aws directory>`
    - `sudo python3 main.py`
- Modify `config.ini` to configure the operation of the weather station