"""
steve.a.mccluskey@gmail.com
Read Adafruit SHT30 Humidity and Temperature Sensor data and write to InfluxDB.
This uses SMBus (System Management Bus), a subset of the I2C (Inter-Integrated Circuit) protocol.
"""

import os
import socket
import struct
import time
from dotenv import load_dotenv
import smbus
from influxdb import InfluxDBClient
from influxdb.exceptions import InfluxDBServerError
from constants import HUMIDITY_TEMP_SENSOR_TYPE as SENSOR_TYPE

DEBUG = False  # set to True to print query result

HOSTNAME = socket.gethostname()

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
SENSOR_DATABASE = os.getenv("SENSOR_DATABASE")

SENSOR_LOCATION = os.getenv("HUMIDITY_TEMP_SENSOR_LOCATION")
SENSOR_ID = os.getenv("HUMIDITY_TEMP_SENSOR_ID")
SENSOR_TITLE = os.getenv("HUMIDITY_TEMP_SENSOR_TITLE")

I2C_ADDR = 0x44
WRITE_REGISTER = 0x2C
READ_REGISTER = 0x00
WRITE_DATA = [0x06]
LENGTH_BYTES = 6

print("Connecting to the database")
client = InfluxDBClient(INFLUXDB_HOST, INFLUXDB_PORT, USERNAME, PASSWORD, SENSOR_DATABASE)
databases = client.get_list_database()
if not any(db['name'] == SENSOR_DATABASE for db in databases):
    print(f"Creating {SENSOR_DATABASE}")
    client.create_database(SENSOR_DATABASE)
    client.switch_database(SENSOR_DATABASE)
print(f"InfluxDB client ok! Using {SENSOR_DATABASE}")

bus = smbus.SMBus(1)

while True:
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
        client.write_points(series)
        print("Series written to InfluxDB.")

        if DEBUG is True:
            query_result = client.query('SELECT * FROM "temps" WHERE time >= now() - 10s')
            print(f"Query results: {query_result}")

    except InfluxDBServerError as e:
        print("Failure writing to or reading from InfluxDB:", e)

    time.sleep(10)
