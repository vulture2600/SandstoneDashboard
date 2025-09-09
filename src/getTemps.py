"""
Read Adafruit 1-Wire temperature sensor data and write to InfluxDB.
Requires .env or .env.<hostname> file for SMB, InfluxDB, and log level.
Developers: steve.a.mccluskey@gmail.com, see repo for others.
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

class GetTempSensors:
    """Get assigned and attached temperature sensors and combine into a room/sensor map"""

    def __init__(self, json_config, hostname):
        self.json_config = json_config
        self.hostname = hostname
        self.rooms = {}
        self.sensor_ids = []
        self.unassigned_ids = []

    def get_assigned_sensors(self):
        """Get room assigned sensors for the host from the config file"""
        if self.json_config:
            self.rooms = self.json_config.get(self.hostname)

            if self.rooms is None:
                logging.warning(f"Hostname not found in {CONFIG_FILE_NAME}")
            elif not self.rooms:
                logging.warning(f"No rooms for {self.hostname} found in {CONFIG_FILE_NAME}")
            else:
                logging.info(f"Sensors in {CONFIG_FILE_NAME}: {len(self.rooms)}")

    def get_attached_sensors(self):
        """Get sensors attached to the host"""
        try:
            self.sensor_ids = os.listdir(DEVICES_PATH)
            self.sensor_ids = [sensor_id for sensor_id in self.sensor_ids if sensor_id.startswith(SENSOR_PREFIX)]
            logging.info(f"Attached sensors: {len(self.sensor_ids)}")
        except Exception as e:
            logging.error(f"Cannot list {DEVICES_PATH} - {e}")
            self.sensor_ids = []

    def find_unassigned_sensors(self):
        """
        Find sensors attached to the host that are not in the config file.
        Log sensors in the config file that are not attached to the host.
        """
        if self.rooms is None:
            self.rooms = {}
        ids_from_config = {room['id'] for room in self.rooms.values()}

        self.unassigned_ids = [sid for sid in self.sensor_ids if sid not in ids_from_config]
        logging.info(f"Attached unassigned sensors: {len(self.unassigned_ids)}")
        for unassigned_sensor in self.unassigned_ids:
            logging.info(f"Attached unassigned: {unassigned_sensor}")

        assigned_unattached_ids = [sid for sid in ids_from_config if sid not in self.sensor_ids]
        logging.info(f"Assigned unattached sensors: {len(assigned_unattached_ids)}")
        for assigned_unattached_id in assigned_unattached_ids:
            logging.info(f"Assigned unattached sensor: {assigned_unattached_id}")

    def combine_unassigned_assigned(self):
        """
        Add the unassigned attached sensors to the assigned sensors from the config file.
        This adds to self.rooms
        """
        for idx, sid in enumerate(self.unassigned_ids, start=1):
            key = f"Unassigned{idx}"
            self.rooms[key] = {"id": sid, "title": "Untitled"}
        logging.info(f"All sensors: {len(self.rooms)}")

    def run(self) -> dict:
        """Run all methods of GetTempSensors"""
        self.get_assigned_sensors()
        self.get_attached_sensors()
        self.find_unassigned_sensors()
        self.combine_unassigned_assigned()
        return self.rooms

class TempUtils:
    """Read temperatures from device files and construct data points"""

    @staticmethod
    def read_temp(device_file: str) -> float:
        """
        Read temperature from device file written to by 1-Wire temp sensor.
        Exp device file: /sys/bus/w1/devices/28-01154f230fa5/w1_slave

        Exp line1: 2b 01 4b 46 7f ff 7f 10 51 : crc=51 YES
        Exp line2: 2b 01 4b 46 7f ff 7f 10 51 t=18687
        """

        marker = "t="
        logging.info(f"Device file: {device_file}")

        try:
            with open(device_file, "r") as f:
                lines = f.readlines()

            if len(lines) < 2:
                logging.error(f"Temperature not found in {device_file}")
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

    @staticmethod
    def construct_data_point(room_id, sensor_id, title, status, hostname, temp) -> dict:
        """Construct the data point"""
        return {
            "measurement": "temps",
            "tags": {
                "location": room_id,
                "id": sensor_id,
                "type": TEMP_SENSOR_MODEL,
                "title": title,
                "status": status,
                "hostname": hostname
            },
            "fields": {
                "temp_flt": temp
            }
        }

def write_points_to_series(room_sensor_map, hostname) -> list[dict]:
    """Read all devices files and construct data points"""

    point_series = []
    working_sensor_count = 0
    for room_id in room_sensor_map:

        status = "On"
        sensor_id = room_sensor_map.get(room_id, {}).get('id')
        temp = TempUtils.read_temp(f"{DEVICES_PATH}{sensor_id}/{W1_SLAVE_FILE}")

        if temp:
            working_sensor_count += 1
        else:
            status = "OFF"
            temp = -999.9

        title = room_sensor_map.get(room_id, {}).get('title')
        if not title:
            title = "Untitled"

        point = TempUtils.construct_data_point(room_id, sensor_id, title, status, hostname, temp)
        logging.debug(f"Point: {point}")
        point_series.append(point)

    logging.info(f"Working sensors: {working_sensor_count}")
    return point_series

if __name__ == "__main__":

    HOSTNAME = socket.gethostname()
    choose_dotenv(HOSTNAME)

    LOG_LEVEL = os.getenv("LOG_LEVEL_GET_TEMPS", "INFO").upper()
    LOG_FILE = os.getenv("LOG_FILE_GET_TEMPS", "/var/log/getTemps.log")
    FORMAT = '%(asctime)-15s %(levelname)s %(message)s'
    numeric_level = getattr(logging, LOG_LEVEL, logging.INFO)
    logging.basicConfig(filename=LOG_FILE, level=numeric_level, format=FORMAT)
    print(f"Logging to {LOG_FILE}")

    logging.info(f"Python version: {sys.version}")

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
        ["modprobe", KERNEL_MOD_W1_GPIO], capture_output=True, text=True, check=False))
    kernel_mod_loads.append(subprocess.run(
        ["modprobe", KERNEL_MOD_W1_THERM], capture_output=True, text=True, check=False))

    KERNEL_MOD_LOAD_FAIL = False

    for kernel_mod_load in kernel_mod_loads:
        if kernel_mod_load.returncode != 0:
            err_msg = (kernel_mod_load.stderr or "").strip() or "No stderr output"
            logging.critical(f"Kernel module load failed: {err_msg}", exc_info=True)
            KERNEL_MOD_LOAD_FAIL = True

    if KERNEL_MOD_LOAD_FAIL:
        logging.critical("Exiting due to kernel module load failure(s)", exc_info=True)
        db_client.close()
        sys.exit(1)

    try:
        while True:

            logging.info(f"Updating {CONFIG_FILE_NAME} if missing or old")
            GET_JSON_SUCCESSFUL = smb_client.get_json_config()

            logging.info(f"Loading {CONFIG_FILE_NAME}")
            loaded_json_config = load_json_file(CONFIG_FILE)

            temp_sensors = GetTempSensors(loaded_json_config, HOSTNAME)
            room_temp_sensor_map = temp_sensors.run()

            logging.info("Reading temperatures from device files...")
            data_point_series = write_points_to_series(room_temp_sensor_map, HOSTNAME)

            try:
                db_client.write_points(data_point_series)
                logging.info("Series written to InfluxDB.")

                if LOG_LEVEL == 'DEBUG':
                    query_result = db_client.query('SELECT * FROM "temps" WHERE time >= now() - 5s')
                    logging.debug(f"Query results: {query_result}")

            except (InfluxDBServerError, InfluxDBClientError, RequestsConnectionError, Timeout) as e:
                logging.error(f"Failure writing to or reading from InfluxDB: {e}")
                db_client = database_connect(INFLUXDB_HOST, INFLUXDB_PORT, USERNAME, PASSWORD, DATABASE)

            if GET_JSON_SUCCESSFUL is False:
                smb_client.connect()

            time.sleep(5)

    except KeyboardInterrupt:
        logging.info("Exiting gracefully")
        print()
    finally:
        db_client.close()
