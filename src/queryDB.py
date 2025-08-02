"""
File to get master config file from NAS, read all 1-wire sensors, and post to InfluxDB.
This is a refactored version of the original getTemps.py script.
steve.a.mccluskey@gmail.com
"""

import datetime
import json
import os
import socket
import subprocess
import sys
import threading
import time
from os import path
from dotenv import load_dotenv
from influxdb import InfluxDBClient
from smb.SMBConnection import SMBConnection
from constants import DEVICES_PATH, W1_SLAVE_FILE, KERNEL_MOD_W1_GPIO, KERNEL_MOD_W1_THERM, TEMP_SENSOR_MODEL

DEBUG = True
RUN_CONTINUE = False # set to True to run continuously, False to run once and exit

HOSTNAME = socket.gethostname()

APP_ENV = os.getenv("APP_ENV")

if 'INVOCATION_ID' in os.environ:
    print(f"Running under Systemd, using .env.{HOSTNAME} file")
    load_dotenv(override=True, dotenv_path=f".env.{HOSTNAME}")
else:
    print("Using .env file")
    load_dotenv(override=True)

INFLUXDB_HOST = os.getenv("INFLUXDB_HOST")
INFLUXDB_PORT = os.getenv("INFLUXDB_PORT")
USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")
TEMP_SENSOR_DATABASE = os.getenv("SENSOR_DATABASE")

MASTER_CONFIG_FILE = os.getenv("MASTER_CONFIG_FILE")
LOCAL_CONFIG_FILE = os.getenv('LOCAL_CONFIG_FILE')
SMB_SERVER = os.getenv("SMB_SERVER_IP")
SMB_SHARE = os.getenv("SMB_SHARE_NAME")
SMB_USER = os.getenv("SMB_USERNAME")
SMB_PASSWORD = os.getenv("SMB_PASSWORD")

DEGREE_SIGN = "\N{DEGREE SIGN}"

print("Verifying all kernel modules are loaded.")
kernel_mod_loads = []
kernel_mod_loads.append(subprocess.run(["modprobe", KERNEL_MOD_W1_GPIO], capture_output=True, text=True))
kernel_mod_loads.append(subprocess.run(["modprobe", KERNEL_MOD_W1_THERM], capture_output=True, text=True))

KERNEL_MOD_LOAD_FAIL = False

client = InfluxDBClient(INFLUXDB_HOST, INFLUXDB_PORT, USERNAME, PASSWORD, TEMP_SENSOR_DATABASE)
client.create_database(TEMP_SENSOR_DATABASE)
client.get_list_database()
client.switch_database(TEMP_SENSOR_DATABASE)
print("InfluxDB Client OK!")

for kernel_mod_load in kernel_mod_loads:
    if kernel_mod_load.returncode != 0:
        print(kernel_mod_load.stderr.rstrip())
        KERNEL_MOD_LOAD_FAIL = True

if KERNEL_MOD_LOAD_FAIL is True:
    print("Exiting")
    sys.exit(1)

## Delete read_temp() if it's no longer being used


try:


    result = client.query('select * from "raw_data" where time >= now() - 5s and time <= now()')

    if DEBUG is True:
        print("Query recieved.")
        print(result)
        print(" ")

except InfluxDBServerError as e:
    print("server failed, reason: " + str(e))
    print(" ")



 
