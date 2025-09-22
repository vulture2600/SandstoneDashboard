"""
steve.a.mccluskey@gmail.com
Read Adafruit SHT30 Humidity and Temperature Sensor data and write to InfluxDB.
This uses SMBus (System Management Bus), a subset of the I2C (Inter-Integrated Circuit) protocol.
"""

import os
import logging
import socket
import struct
import sys
import time
import smbus2
from requests.exceptions import Timeout
from requests.exceptions import ConnectionError as RequestsConnectionError
from influxdb.exceptions import InfluxDBServerError, InfluxDBClientError
from constants import HUMIDITY_TEMP_SENSOR_TYPE as SENSOR_TYPE
from common_functions import choose_dotenv, database_connect, SMBFileTransfer, load_json_file

WRITE_REGISTER = 0x2C
READ_REGISTER = 0x00
WRITE_DATA = [0x06]
LENGTH_BYTES = 6

CONFIG_FILE_TRY_AGAIN_SECS = 60
CONFIG_FILE_NAME = "getSHT30.json"
CONFIG_FILE = f"config/{CONFIG_FILE_NAME}"

HOSTNAME = socket.gethostname()
choose_dotenv(HOSTNAME)

LOG_LEVEL = os.getenv("LOG_LEVEL_GET_SHT30", "INFO").upper()
LOG_FILE = os.getenv("LOG_FILE_GET_SHT30", "/var/log/getSHT30.log")
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

bus = smbus2.SMBus(1)

try:
    while True:

        logging.info(f"Updating {CONFIG_FILE_NAME} if old or missing")
        GET_JSON_SUCCESSFUL = smb_client.get_json_config()

        logging.info(f"Loading {CONFIG_FILE_NAME}")
        json_config = load_json_file(CONFIG_FILE)

        if json_config is None:
            logging.warning(f"Trying again in {CONFIG_FILE_TRY_AGAIN_SECS} seconds")
            time.sleep(CONFIG_FILE_TRY_AGAIN_SECS)
            continue

        SENSORS = json_config.get(HOSTNAME)

        if SENSORS is None:
            logging.warning(f"Hostname not found in {CONFIG_FILE_NAME}")
            logging.warning(f"Trying again in {CONFIG_FILE_TRY_AGAIN_SECS} seconds")
            time.sleep(CONFIG_FILE_TRY_AGAIN_SECS)
            continue

        if not SENSORS:
            logging.warning(f"No sensors for {HOSTNAME} found in {CONFIG_FILE_NAME}")
            logging.warning(f"Trying again in {CONFIG_FILE_TRY_AGAIN_SECS} seconds")
            time.sleep(CONFIG_FILE_TRY_AGAIN_SECS)
            continue

        sensor_count = len(SENSORS)
        logging.info(f"Sensors in {CONFIG_FILE_NAME}: {sensor_count}")

        if sensor_count > 1:
            logging.warning(f"More than one sensor found for {HOSTNAME} in {CONFIG_FILE_NAME}")
            logging.warning("Not currently handling multiple SHT30 sensors per host")
            logging.warning(f"Trying again in {CONFIG_FILE_TRY_AGAIN_SECS} seconds")
            time.sleep(CONFIG_FILE_TRY_AGAIN_SECS)
            continue

        SENSOR_LOCATION = list(SENSORS.keys())[0]
        SENSOR_ID = SENSORS[SENSOR_LOCATION]["id"]
        I2C_ADDR = int(SENSOR_ID.split(':')[1], 16)
        SENSOR_TITLE = SENSORS[SENSOR_LOCATION]["title"]

        series = []
        logging.info("Reading SHT30 sensors")

        try:
            logging.info("Writing to I2C bus")
            bus.write_i2c_block_data(I2C_ADDR, WRITE_REGISTER, WRITE_DATA)
            time.sleep(0.5)
            logging.info("Reading from I2C bus")
            i2c_block_data = bus.read_i2c_block_data(I2C_ADDR, READ_REGISTER, LENGTH_BYTES)

            logging.info(f"I2C block data: {i2c_block_data}")

            if len(i2c_block_data) < 5:
                logging.error("I2C block data has fewer than 4 items.")
                continue

            temp_MSB, temp_LSB = i2c_block_data[0:2]
            humidity_MSB, humidity_LSB = i2c_block_data[3:5]

            raw_temp = struct.unpack(">H", bytes([temp_MSB, temp_LSB]))[0]
            temp_C = -45 + (175 * raw_temp / 65535.0)
            temp_F = temp_C * 1.8 + 32

            raw_hum = struct.unpack(">H", bytes([humidity_MSB, humidity_LSB]))[0]
            humidity = 100 * raw_hum / 65535.0

            point = {
                "measurement": "temps",

                "tags": {
                    "sensor":   1,
                    "location": SENSOR_LOCATION,
                    "id":       SENSOR_ID,
                    "type":     SENSOR_TYPE,
                    "title":    SENSOR_TITLE,
                    "hostname": HOSTNAME,
                    "status":   "ON"
                },
                "fields": {
                    "temp_flt": temp_F,
                    "humidity_flt": humidity
                }
            }
            logging.debug(f"Point: {point}")
            series.append(point)

        except OSError as e:
            logging.error(f"I2C read failed: {e}")
            continue
        except Exception as e:
            logging.error(f"Unexpected error: {e}")
            continue

        try:
            db_client.write_points(series)
            logging.info("Series written to InfluxDB.")

            if LOG_LEVEL == 'DEBUG':
                query_result = db_client.query('SELECT * FROM "temps" WHERE time >= now() - 10s')
                logging.debug(f"Query results: {query_result}")

        except (InfluxDBServerError, InfluxDBClientError, RequestsConnectionError, Timeout) as e:
            logging.error(f"Failure writing to or reading from InfluxDB: {e}")
            db_client = database_connect(INFLUXDB_HOST, INFLUXDB_PORT, USERNAME, PASSWORD, DATABASE)

        if GET_JSON_SUCCESSFUL is False:
            smb_client.connect()

        time.sleep(10)

except KeyboardInterrupt:
    logging.info("Exiting gracefully")
    print()
finally:
    bus.close()
    db_client.close()
