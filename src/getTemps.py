"""
steve.a.mccluskey@gmail.com
Read Adafruit 1-Wire temperature sensor data and write to InfluxDB. See .env files for required config file.
"""

# This file will be merged with getTemps.py from branch master_config_file.

import os
import socket
import time
import sys
import subprocess
from dotenv import load_dotenv
from influxdb.exceptions import InfluxDBServerError
from constants import DEVICES_PATH, W1_SLAVE_FILE, KERNEL_MOD_W1_GPIO, KERNEL_MOD_W1_THERM, TEMP_SENSOR_MODEL
from common_functions import database_connect, load_json_file

DEBUG = False  # set to True to print query result

HOSTNAME = socket.gethostname()
CONFIG_FILE = "config/getTemps.json"
CONFIG_FILE_TRY_AGAIN_SECS = 60
SLEEP_MINUTES = CONFIG_FILE_TRY_AGAIN_SECS / 60
SLEEP_MINUTES_FORMATTED = f"{SLEEP_MINUTES:.1f}".rstrip("0").rstrip(".")

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
DATABASE = os.getenv("SENSOR_DATABASE")

db_client = database_connect(INFLUXDB_HOST, INFLUXDB_PORT, USERNAME, PASSWORD, DATABASE)

print("Verifying all kernel modules are loaded")
kernel_mod_loads = []
kernel_mod_loads.append(subprocess.run(["modprobe", KERNEL_MOD_W1_GPIO], capture_output=True, text=True))
kernel_mod_loads.append(subprocess.run(["modprobe", KERNEL_MOD_W1_THERM], capture_output=True, text=True))

KERNEL_MOD_LOAD_FAIL = False

for kernel_mod_load in kernel_mod_loads:
    if kernel_mod_load.returncode != 0:
        print(kernel_mod_load.stderr.rstrip())
        KERNEL_MOD_LOAD_FAIL = True

if KERNEL_MOD_LOAD_FAIL is True:
    print("Exiting")
    sys.exit(1)

def read_temp(device_file):
    """Read temperature from 1-Wire temp sensor attached to the system bus"""

    marker = "t="
    print(f"Device file: {device_file}")

    try:
        with open(device_file, "r") as f:
            lines = f.readlines()

        if len(lines) < 2:
            print("Error: Device file has fewer than 2 lines.")
            return None

        print(f"Device file lines: {lines}")
        line = lines[1].strip()
        position = line.find(marker)

        if position == -1:
            print(f"Error: Marker '{marker}' not found in line: {line}")
            return None

        temp_string = line[position + len(marker):]
        temp_C = float(temp_string) / 1000.0
        temp_F = round(temp_C * 1.8 + 32, 1)
        return temp_F

    except FileNotFoundError as e:
        print(f"File not found: {device_file} — {e}")
    except ValueError as e:
        print(f"Error parsing temperature value: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

    return None

while True:

    print("Loading config file")
    ROOMS = load_json_file(CONFIG_FILE).get(HOSTNAME)
    if ROOMS is None:
        print(f"Hostname not found in {CONFIG_FILE}")
        print(f"Trying again in {SLEEP_MINUTES_FORMATTED} minute(s)")
        time.sleep(CONFIG_FILE_TRY_AGAIN_SECS)
        continue

    room_count = len(ROOMS)
    if room_count == 0:
        print(f"No rooms for {HOSTNAME} found in {CONFIG_FILE}")
        print(f"Trying again in {SLEEP_MINUTES_FORMATTED} minute(s)")
        time.sleep(CONFIG_FILE_TRY_AGAIN_SECS)
        continue

    print("Reading Sensors...")
    series = []
    ASSIGNED_SENSOR_COUNT = 0

    for i in range(room_count):

        STATUS = "On"
        room_id = list(ROOMS.keys())[i]
        SENSOR_ID = ROOMS.get(room_id, {}).get('id')
        if SENSOR_ID:
            TEMP 	  = read_temp(f"{DEVICES_PATH}{SENSOR_ID}/{W1_SLAVE_FILE}")
            ASSIGNED_SENSOR_COUNT += 1
        else:
            SENSOR_ID = "unassigned"
            TEMP 	  = None
            STATUS    = "Off"

        TITLE = ROOMS.get(room_id, {}).get('title')
        if not TITLE:
            TITLE = "Untitled"

        point = {
            "measurement": "temps",
            "tags": {
                "sensor": i + 1,
                "location": room_id,
                "id": SENSOR_ID,
                "type": TEMP_SENSOR_MODEL,
                "title": TITLE
            },
            "fields": {
                "status": STATUS,
                "temp_flt": TEMP
            }
        }
        print(f"Point: {point}")
        series.append(point)

    print(f"Assigned sensors: {ASSIGNED_SENSOR_COUNT}")

    try:
        db_client.write_points(series)
        print("Series written to InfluxDB.")

        if DEBUG is True:
            query_result = db_client.query('SELECT * FROM "temps" WHERE time >= now() - 5s')
            print(f"Query results: {query_result}")

    except InfluxDBServerError as e:
        print("Failure writing to or reading from InfluxDB:", e)

    time.sleep(5)
