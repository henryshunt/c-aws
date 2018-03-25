# ICAWS Data Acquisition Program
#  responsible for measuring and logging data parameters, and for generating
#  statistics. All database writes are done here. This is the main ICAWS
#  program and the entry point for the ICAWS software

import config_data

config = config_data.ConfigData()


if __name__ == "__main__":
    config_load = config.load()

    # Cannot start ICAWS software without a configuration
    if config_load == False: system.exit(1)
