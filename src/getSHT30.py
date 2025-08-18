"""
steve.a.mccluskey@gmail.com
Read Adafruit SHT30 Humidity and Temperature Sensor data and write to InfluxDB.
This uses SMBus (System Management Bus), a subset of the I2C (Inter-Integrated Circuit) protocol.
"""

import os
import socket
import struct
import time
import smbus
from requests.exceptions import Timeout
from requests.exceptions import ConnectionError as RequestsConnectionError
from influxdb.exceptions import InfluxDBServerError, InfluxDBClientError
from constants import HUMIDITY_TEMP_SENSOR_TYPE as SENSOR_TYPE
from common_functions import choose_dotenv, database_connect, load_json_file

DEBUG = False  # set to True to print query result

HOSTNAME = socket.gethostname()
CONFIG_FILE = "config/getSHT30.json"
CONFIG_FILE_TRY_AGAIN_SECS = 60

choose_dotenv(HOSTNAME)

INFLUXDB_HOST = os.getenv("INFLUXDB_HOST")
INFLUXDB_PORT = os.getenv("INFLUXDB_PORT")
USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")
DATABASE = os.getenv("SENSOR_DATABASE")

I2C_ADDR = 0x44
WRITE_REGISTER = 0x2C
READ_REGISTER = 0x00
WRITE_DATA = [0x06]
LENGTH_BYTES = 6

db_client = database_connect(INFLUXDB_HOST, INFLUXDB_PORT, USERNAME, PASSWORD, DATABASE)

bus = smbus.SMBus(1)

while True:

    print("Loading config file")
    SENSORS = load_json_file(CONFIG_FILE).get(HOSTNAME)
    if SENSORS is None:
        print(f"Hostname not found in {CONFIG_FILE}")
        print(f"Trying again in {CONFIG_FILE_TRY_AGAIN_SECS} seconds")
        time.sleep(CONFIG_FILE_TRY_AGAIN_SECS)
        continue

    sensor_count = len(SENSORS)

    if sensor_count == 0:
        print(f"No sensors for {HOSTNAME} found in {CONFIG_FILE}")
        print(f"Trying again in {CONFIG_FILE_TRY_AGAIN_SECS} seconds")
        time.sleep(CONFIG_FILE_TRY_AGAIN_SECS)
        continue

    if sensor_count > 1:
        print(f"More than one sensor found for {HOSTNAME} in {CONFIG_FILE}")
        print("Not currently handling multiple SHT30 sensors per host")
        print(f"Trying again in {CONFIG_FILE_TRY_AGAIN_SECS} seconds")
        time.sleep(CONFIG_FILE_TRY_AGAIN_SECS)
        continue

    SENSOR_LOCATION = list(SENSORS.keys())[0]
    SENSOR_ID = SENSORS[SENSOR_LOCATION]["id"]
    SENSOR_TITLE = SENSORS[SENSOR_LOCATION]["title"]

    series = []
    print("Reading SHT30 sensors")

    try:
        print("Writing to I2C bus")
        bus.write_i2c_block_data(I2C_ADDR, WRITE_REGISTER, WRITE_DATA)
        time.sleep(0.5)
        print("Reading from I2C bus")
        i2c_block_data = bus.read_i2c_block_data(I2C_ADDR, READ_REGISTER, LENGTH_BYTES)

        print("I2C block data:", i2c_block_data)

        if len(i2c_block_data) < 5:
            print("Error: I2C block data has fewer than 4 items.")
            continue

        temp_MSB, temp_LSB = i2c_block_data[0:2]
        humidity_MSB, humidity_LSB = i2c_block_data[3:5]

        raw_temp = struct.unpack(">H", bytes([temp_MSB, temp_LSB]))[0]
        temp_C = -45 + (175 * raw_temp / 65535.0)
        temp_F = round(temp_C * 1.8 + 32, 1)

        raw_hum = struct.unpack(">H", bytes([humidity_MSB, humidity_LSB]))[0]
        humidity = round(100 * raw_hum / 65535.0, 1)

        point = {
            "measurement": "temps",

            "tags": {
                "sensor":   1,
                "location": SENSOR_LOCATION,
                "id":       SENSOR_ID,
                "type":     SENSOR_TYPE,
                "title":    SENSOR_TITLE
            },
            "fields": {
                "temp_flt": temp_F,
                "humidity": str(humidity)
            }
        }
        print(f"Point: {point}")
        series.append(point)

    except OSError as e:
        print(f"I2C read failed: {e}")
        continue
    except Exception as e:
        print(f"Unexpected error: {e}")
        continue

    try:
        db_client.write_points(series)
        print("Series written to InfluxDB.")

        if DEBUG is True:
            query_result = db_client.query('SELECT * FROM "temps" WHERE time >= now() - 10s')
            print(f"Query results: {query_result}")

    except (InfluxDBServerError, InfluxDBClientError, RequestsConnectionError, Timeout) as e:
        print("Failure writing to or reading from InfluxDB:", e)
        db_client = database_connect(INFLUXDB_HOST, INFLUXDB_PORT, USERNAME, PASSWORD, DATABASE)

    time.sleep(10)
