"""
steve.a.mccluskey@gmail.com
Read Adafruit 1-Wire temperature sensor data and write to InfluxDB. See .env files for required config file.
"""

import os
import logging
import socket
import time
import sys
import subprocess
from requests.exceptions import Timeout
from requests.exceptions import ConnectionError as RequestsConnectionError
from influxdb.exceptions import InfluxDBServerError, InfluxDBClientError
from constants import DEVICES_PATH, W1_SLAVE_FILE, KERNEL_MOD_W1_GPIO, KERNEL_MOD_W1_THERM, TEMP_SENSOR_MODEL
from common_functions import choose_dotenv, database_connect, SMBFileTransfer, load_json_file

SENSOR_PREFIX = "28-"
CONFIG_FILE_NAME = "getTemps.json"
CONFIG_FILE = f"config/{CONFIG_FILE_NAME}"
LOG_FILE = "/var/log/getTemps.log"

HOSTNAME = socket.gethostname()
choose_dotenv(HOSTNAME)

LOG_LEVEL = os.getenv("LOG_LEVEL_GET_TEMPS", "INFO").upper()
FORMAT = '%(asctime)-15s %(levelname)s %(message)s'
numeric_level = getattr(logging, LOG_LEVEL, logging.INFO)
logging.basicConfig(filename=LOG_FILE, level=numeric_level, format=FORMAT)
print(f"Logging to {LOG_FILE}")

INFLUXDB_HOST = os.getenv("INFLUXDB_HOST")
INFLUXDB_PORT = os.getenv("INFLUXDB_PORT")
USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")
DATABASE = os.getenv("SENSOR_DATABASE")

SMB_SERVER_PORT = int(os.getenv("SMB_SERVER_PORT", "445"))

smb_client = SMBFileTransfer(os.getenv("SMB_SERVER_IP"),
                             SMB_SERVER_PORT,
                             os.getenv("SMB_SHARE_NAME"),
                             os.getenv("SMB_CONFIG_DIR"),
                             os.getenv("SMB_USERNAME"),
                             os.getenv("SMB_PASSWORD"),
                             CONFIG_FILE_NAME,
                             CONFIG_FILE)
smb_client.connect()

db_client = database_connect(INFLUXDB_HOST,
                             INFLUXDB_PORT,
                             USERNAME,
                             PASSWORD,
                             DATABASE)

logging.info("Verifying all kernel modules are loaded")
kernel_mod_loads = []
kernel_mod_loads.append(subprocess.run(
    ["modprobe", KERNEL_MOD_W1_GPIO], capture_output=True, text=True))
kernel_mod_loads.append(subprocess.run(
    ["modprobe", KERNEL_MOD_W1_THERM], capture_output=True, text=True))

KERNEL_MOD_LOAD_FAIL = False

for kernel_mod_load in kernel_mod_loads:
    if kernel_mod_load.returncode != 0:
        err_msg = (kernel_mod_load.stderr or "").strip() or "No stderr output"
        logging.critical(f"Kernel module load failed: {err_msg}")
        KERNEL_MOD_LOAD_FAIL = True

if KERNEL_MOD_LOAD_FAIL:
    logging.critical("Exiting due to kernel module load failure(s)")
    sys.exit(1)

def read_temp(device_file):
    """Read temperature from 1-Wire temp sensor attached to the system bus"""

    marker = "t="
    logging.info(f"Device file: {device_file}")

    try:
        with open(device_file, "r") as f:
            lines = f.readlines()

        if len(lines) < 2:
            logging.error("Device file has fewer than 2 lines.")
            return None

        logging.debug(f"Device file lines: {lines}")
        line = lines[1].strip()
        position = line.find(marker)

        if position == -1:
            logging.error(f"Marker '{marker}' not found in line: {line}")
            return None

        temp_string = line[position + len(marker):]
        temp_C = float(temp_string) / 1000.0
        temp_F = round(temp_C * 1.8 + 32, 1)
        return temp_F

    except FileNotFoundError as e:
        logging.error(f"File not found: {device_file} — {e}")
    except ValueError as e:
        logging.error(f"Error parsing temperature value: {e}")
    except Exception as e:
        logging.error(f"Unexpected error: {e}")

    return None

while True:

    logging.info(f"Updating {CONFIG_FILE_NAME} if old or missing")
    GET_JSON_SUCCESSFUL = smb_client.get_json_config()

    logging.info(f"Loading {CONFIG_FILE_NAME}")
    json_config = load_json_file(CONFIG_FILE)

    ROOMS = {}
    if json_config:
        ROOMS = json_config.get(HOSTNAME)

        if ROOMS is None:
            logging.warning(f"Hostname not found in {CONFIG_FILE_NAME}")
        elif not ROOMS:
            logging.warning(f"No rooms for {HOSTNAME} found in {CONFIG_FILE_NAME}")
        else:
            logging.info(f"Sensors in {CONFIG_FILE_NAME}: {len(ROOMS)}")

    try:
        sensor_ids = os.listdir(DEVICES_PATH)
        sensor_ids = [sensor_id for sensor_id in sensor_ids if sensor_id.startswith(SENSOR_PREFIX)]
        logging.info(f"Attached sensors: {len(sensor_ids)}")
    except Exception as e:
        logging.error(f"Cannot list {DEVICES_PATH} - {e}")
        sensor_ids = []

    if ROOMS is None:
        ROOMS = {}
    ids_from_config = {room['id'] for room in ROOMS.values()}
    unassigned_ids = [sid for sid in sensor_ids if sid not in ids_from_config]
    logging.info(f"Unassigned sensors: {len(unassigned_ids)}")

    for idx, sid in enumerate(unassigned_ids, start=1):
        KEY = f"Unassigned{idx}"
        ROOMS[KEY] = {"id": sid, "title": "Untitled"}

    ROOM_COUNT = len(ROOMS)
    logging.info(f"All sensors: {ROOM_COUNT}")

    series = []
    WORKING_SENSOR_COUNT = 0
    logging.info("Reading 1-Wire temperature sensors...")

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
        logging.debug(f"Point: {point}")
        series.append(point)

    logging.info(f"Working sensors: {WORKING_SENSOR_COUNT}")

    try:
        db_client.write_points(series)
        logging.info("Series written to InfluxDB.")

        if LOG_LEVEL == 'DEBUG':
            query_result = db_client.query('SELECT * FROM "temps" WHERE time >= now() - 5s')
            logging.debug(f"Query results: {query_result}")

    except (InfluxDBServerError, InfluxDBClientError, RequestsConnectionError, Timeout) as e:
        logging.error("Failure writing to or reading from InfluxDB:", e)
        db_client = database_connect(INFLUXDB_HOST, INFLUXDB_PORT, USERNAME, PASSWORD, DATABASE)

    if GET_JSON_SUCCESSFUL is False:
        smb_client.connect()

    time.sleep(5)
