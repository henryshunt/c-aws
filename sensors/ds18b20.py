import os

def read_temperature(address, store):
    """ Reads the value of a DS18B20 temperature probe via its address, into
        the specified variable
    """
    if not os.path.isdir("/sys/bus/w1/devices/" + address):
        if store != None: store = None
        return None

    try:
        # Read the probe and convert its value to a degC float
        with open("/sys/bus/w1/devices/" + address + "/w1_slave", "r"
                ) as probe:
            data = probe.readlines()
            temp = int(data[1][data[1].find("t=") + 2:]) / 1000

            # Check for error values
            if temp == -127 or temp == 85:
                if store != None: store = None
                return None

            if store != None: store = temp
            return temp

    except:
        if store != None: store = None
        return None