"""
steve.a.mccluskey@gmail.com
Read Adafruit SHT30 Humidity and Temperature Sensor data and write to InfluxDB.
This uses SMBus (System Management Bus), a subset of the I2C (Inter-Integrated Circuit) protocol.
"""

import os
import socket
import time
from dotenv import load_dotenv
import smbus
from influxdb import InfluxDBClient
from constants import HUMIDITY_TEMP_SENSOR_TYPE as SENSOR_TYPE

# Set to True to print query result:
DEBUG = False

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
    print("Reading Sensors:")
    try:
        series = []
        bus.write_i2c_block_data(0x44, 0x2C, [0x06])
        time.sleep(0.5)
        data1 = bus.read_i2c_block_data(0x44, 0x00, 6)

        cTemp = ((((data1[0] * 256.0) + data1[1]) * 175) / 65535.0) - 45
        fTemp = format(float((cTemp * 1.8) + 32), '.1f')
        print(str(fTemp), "F")

        humidity = format(float(100 * (data1[3] * 256 + data1[4]) / 65535.0), '.1f')
        print(str(humidity), "%")

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
                "temp_flt": float(fTemp),
                "humidity": humidity
            }
        }

        series.append(point)
    except:
        print("SHT30 not responding.")

    try:
        client.write_points(series)
        print("Data posted to DB.")

        result = client.query('select * from "temps" where time >= now() - 5s and time <= now()')
        print("Query received")
        if DEBUG is True:
            print(result)
    except:
        print("Server timeout")

    time.sleep(10)
