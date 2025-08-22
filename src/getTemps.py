"""
steve.a.mccluskey@gmail.com
Read Adafruit 1-Wire temperature sensor data and write to InfluxDB. See .env files for required config file.
"""

import os
import socket
import time
import sys
import subprocess
from requests.exceptions import Timeout
from requests.exceptions import ConnectionError as RequestsConnectionError
from influxdb.exceptions import InfluxDBServerError, InfluxDBClientError
from constants import DEVICES_PATH, W1_SLAVE_FILE, KERNEL_MOD_W1_GPIO, KERNEL_MOD_W1_THERM, TEMP_SENSOR_MODEL
from common_functions import choose_dotenv, database_connect, SMBFileTransfer, load_json_file

DEBUG = False  # set to True to print query result

SENSOR_PREFIX = "28-"
CONFIG_FILE_NAME = "getTemps.json"
CONFIG_FILE = f"config/{CONFIG_FILE_NAME}"

HOSTNAME = socket.gethostname()
choose_dotenv(HOSTNAME)

SMB_SERVER_IP = os.getenv("SMB_SERVER_IP")
SMB_SERVER_PORT = os.getenv("SMB_SERVER_PORT")
SMB_SHARE_NAME = os.getenv("SMB_SHARE_NAME")
SMB_CONFIG_DIR = os.getenv("SMB_CONFIG_DIR")
SMB_USERNAME = os.getenv("SMB_USERNAME")
SMB_PASSWORD = os.getenv("SMB_PASSWORD")

INFLUXDB_HOST = os.getenv("INFLUXDB_HOST")
INFLUXDB_PORT = os.getenv("INFLUXDB_PORT")
USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")
DATABASE = os.getenv("SENSOR_DATABASE")

smb_client = SMBFileTransfer(SMB_SERVER_IP,
                             SMB_SERVER_PORT,
                             SMB_SHARE_NAME,
                             SMB_CONFIG_DIR,
                             CONFIG_FILE_NAME,
                             CONFIG_FILE,
                             SMB_USERNAME,
                             SMB_PASSWORD)
smb_client.connect()

db_client = database_connect(INFLUXDB_HOST,
                             INFLUXDB_PORT,
                             USERNAME,
                             PASSWORD,
                             DATABASE)

print("Verifying all kernel modules are loaded")
kernel_mod_loads = []
kernel_mod_loads.append(subprocess.run(
    ["modprobe", KERNEL_MOD_W1_GPIO], capture_output=True, text=True))
kernel_mod_loads.append(subprocess.run(
    ["modprobe", KERNEL_MOD_W1_THERM], capture_output=True, text=True))

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

    print(f"Updating {CONFIG_FILE_NAME} if needed")
    GET_JSON_SUCCESSFUL = smb_client.get_json_config()
    # print(f"Get JSON Success: {GET_JSON_SUCCESSFUL}")

    print(f"Loading {CONFIG_FILE_NAME}")
    ROOMS = load_json_file(CONFIG_FILE).get(HOSTNAME)
    ROOM_COUNT = 0

    if ROOMS is None:
        print(f"Hostname not found in {CONFIG_FILE_NAME}")
    else:
        ROOM_COUNT = len(ROOMS)

    if ROOM_COUNT == 0:
        print(f"No rooms for {HOSTNAME} found in {CONFIG_FILE_NAME}")
    else:
        print(f"Sensors in {CONFIG_FILE_NAME}: {ROOM_COUNT}")

    try:
        sensor_ids = os.listdir(DEVICES_PATH)
    except Exception as e:
        print(f"Cannot list {DEVICES_PATH} - {e}")
    sensor_ids = [sensor_id for sensor_id in sensor_ids if sensor_id.startswith(SENSOR_PREFIX)]
    print(f"Attached sensors: {len(sensor_ids)}")

    ids_from_config = {room['id'] for room in ROOMS.values()}
    unassigned_ids = [sid for sid in sensor_ids if sid not in ids_from_config]
    print("Unassigned sensors:", len(unassigned_ids))

    for idx, sid in enumerate(unassigned_ids, start=1):
        KEY = f"Unassigned{idx}"
        ROOMS[KEY] = {"id": sid, "title": "Untitled"}

    ROOM_COUNT = len(ROOMS)
    print(f"All sensors: {ROOM_COUNT}")

    series = []
    WORKING_SENSOR_COUNT = 0
    print("Reading 1-Wire temperature sensors...")

    for i in range(ROOM_COUNT):

        STATUS    = "On"
        room_id   = list(ROOMS.keys())[i]
        SENSOR_ID = ROOMS.get(room_id, {}).get('id')
        TEMP 	  = read_temp(f"{DEVICES_PATH}{SENSOR_ID}/{W1_SLAVE_FILE}")

        if TEMP:
            WORKING_SENSOR_COUNT += 1
        else:
            STATUS = "Off"

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
                "title": TITLE,
                "status": STATUS,
                "hostname": HOSTNAME
            },
            "fields": {
                "temp_flt": TEMP
            }
        }
        print(f"Point: {point}")
        series.append(point)

    print(f"Working sensors: {WORKING_SENSOR_COUNT}")

    try:
        db_client.write_points(series)
        print("Series written to InfluxDB.")

        if DEBUG is True:
            query_result = db_client.query('SELECT * FROM "temps" WHERE time >= now() - 5s')
            print(f"Query results: {query_result}")

    except (InfluxDBServerError, InfluxDBClientError, RequestsConnectionError, Timeout) as e:
        print("Failure writing to or reading from InfluxDB:", e)
        db_client = database_connect(INFLUXDB_HOST, INFLUXDB_PORT, USERNAME, PASSWORD, DATABASE)

    if GET_JSON_SUCCESSFUL is False:
        smb_client.connect()

    time.sleep(5)
