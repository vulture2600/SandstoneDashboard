"""
Read Adafruit ADC (Analog-to-Digital Converter) breakout board and write to InfluxDB.
This uses the I2C (Inter-Integrated Circuit) protocol to get water pressure readings.
Developers: steve.a.mccluskey@gmail.com, see repo for others.
"""

# This script will be updated to use a pressure sensor config file

import os
import logging
import socket
import sys
import time
import Adafruit_ADS1x15
from requests.exceptions import Timeout
from requests.exceptions import ConnectionError as RequestsConnectionError
from influxdb.exceptions import InfluxDBServerError, InfluxDBClientError
from constants import PRESSURE_SENSOR_TYPE
from common_functions import choose_dotenv, database_connect

HOSTNAME = socket.gethostname()
choose_dotenv(HOSTNAME)

LOG_LEVEL = os.getenv("LOG_LEVEL_GET_PRESSURES", "INFO").upper()
LOG_FILE = os.getenv("LOG_FILE_GET_PRESSURES", "/var/log/getPressures.log")
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

db_client = database_connect(INFLUXDB_HOST,
                             INFLUXDB_PORT,
                             USERNAME,
                             PASSWORD,
                             DATABASE)

channel0ID   = "schoolRoomDump"
channel0name = "School Room Dump Pressure"
channel0     = 0
ch0GAIN      = 1.0
ch0maxPSI    = 100
ch0minPSI    = 0
ch0minADC    = 4000
ch0maxADC    = 32760
ch0enabled   = "Enabled"

channel1ID   = "upperSchoolRoom"
channel1name = "Upper School Room Pressure"
channel1     = 1
ch1GAIN      = 1.0
ch1maxPSI    = 100
ch1minPSI    = 0
ch1minADC    = 4000
ch1maxADC    = 15000
ch1enabled   = "Enabled"

channel2ID   = "bootyWall"
channel2name = "Booty Wall Pressure"
channel2     = 2
ch2GAIN      = 1.0
ch2maxPSI    = 100
ch2minPSI    = 0
ch2minADC    = 4000
ch2maxADC    = 12000
ch2enabled   = "Enabled"

channel3ID   = "none"
channel3name = "none"
channel3     = 3
ch3GAIN      = 1.0
ch3maxPSI    = 100
ch3minPSI    = 0
ch3minADC    = 4000
ch3maxADC    = 29500
ch3enabled   = "Disabled"

PRESSURE_SENSOR_ID = "i2c:0x48"
I2C_ADDR = int(PRESSURE_SENSOR_ID.split(':')[1], 16)

adc = Adafruit_ADS1x15.ADS1115(address=I2C_ADDR, busnum=1)

while True:
    logging.info("Reading ADC:")
    series = []
    try:
        if ch0enabled == "Enabled":
            logging.info(f"Reading channel {channel0}...")
            #value0  = adc.read_adc(0, gain = 1)
            value0  = adc.read_adc(channel0, gain = ch0GAIN)
            psi0 = format((((value0 - ch0minADC) * (ch0maxPSI - ch0minPSI)) / (ch0maxADC - ch0minADC) + ch0minPSI), '.1f')
            if float(psi0) < 0.2:
                psi0 = "Off"
            logging.info(f"{psi0} {value0} {channel0}")
        else:
            psi0 = "OFF"
            logging.info(f"{psi0}, channel {channel0} disabled.")

        if ch1enabled == "Enabled":
            logging.info(f"Reading channel {channel1}...")
            value1 = adc.read_adc(channel1, gain = ch1GAIN)
            psi1 = format((((value1 - ch1minADC) * (ch1maxPSI - ch1minPSI)) / (ch1maxADC - ch1minADC) + ch1minPSI), '.1f')
            if float(psi1) < 0.2:
                psi1 = "Off"
            logging.info(f"{psi1} {value1} {channel1}")
        else:
            psi1 = "OFF"
            logging.info(f"{psi1}, channel {channel1} disabled.")

        if ch2enabled == "Enabled":
            logging.info(f"Reading channel {channel2}...")
            value2 = adc.read_adc(channel2, gain = ch2GAIN)
            psi2 = format((((value2 - ch2minADC) * (ch2maxPSI - ch2minPSI)) / (ch2maxADC - ch2minADC) + ch2minPSI), '.1f')
            if float(psi2) < 0.2:
                psi2 = "Off"
            logging.info(f"{psi2} {value2}, channel2")
        else:
            psi2 = "OFF"
            logging.info(f"{psi2}, channel {channel2} disabled.")

        if ch3enabled == "Enabled":
            logging.info(f"Reading channel {channel3}...")
            value3 = adc.read_adc(channel3, gain = ch2GAIN)
            psi3 = format((((value3 - ch3minADC) * (ch3maxPSI - ch2minPSI)) / (ch3maxADC - ch3minADC) + ch3minPSI), '.1f')
            if float(psi3) < 0.2:
                psi3 = "Off"
            logging.info(psi3, value3, channel3)
        else:
            psi3 = "OFF"
            logging.info(f"{psi3}, channel {channel3} disabled.")

        point = {
            "measurement": "pressures",
            "tags": {
                "sensor":   0,
                "location": channel0ID,
                "title":    channel0name,
                "id":       PRESSURE_SENSOR_ID,
                "channel":  channel0,
                "type":     PRESSURE_SENSOR_TYPE,
                "hostname": HOSTNAME
            },
            "fields": {
                "pressure": psi0
            }
        }
        logging.debug(f"Point: {point}")
        series.append(point)

        point = {
            "measurement": "pressures",
            "tags": {
                "sensor":   1,
                "location": channel1ID,
                "title":    channel1name,
                "id":       PRESSURE_SENSOR_ID,
                "channel":  channel1,
                "type":     PRESSURE_SENSOR_TYPE,
                "hostname": HOSTNAME
            },
            "fields": {
                "pressure": psi1
            }
        }
        logging.debug(f"Point: {point}")
        series.append(point)

        point = {
            "measurement": "pressures",
            "tags": {
                "sensor":   2,
                "location": channel2ID,
                "title":    channel2name,
                "id":       PRESSURE_SENSOR_ID,
                "channel":  channel2,
                "type":     PRESSURE_SENSOR_TYPE,
                "hostname": HOSTNAME
            },
            "fields": {
                "pressure": psi2
            }
        }
        logging.debug(f"Point: {point}")
        series.append(point)

        point = {
            "measurement": "pressures",
            "tags": {
                "sensor":   3,
                "location": channel3ID,
                "title":    channel3name,
                "id":       PRESSURE_SENSOR_ID,
                "channel":  channel3,
                "type":     PRESSURE_SENSOR_TYPE,
                "hostname": HOSTNAME
            },
            "fields": {
                "pressure": psi3
            }
        }
        logging.debug(f"Point: {point}")
        series.append(point)

    except:
        logging.error("ADC not responding.")
        continue

    try:
        db_client.write_points(series)
        logging.info("Series written to InfluxDB.")

        if LOG_LEVEL == 'DEBUG':
            query_result = db_client.query('SELECT * FROM "pressures" WHERE time >= now() - 5s')
            logging.debug(f"Query results: {query_result}")

    except (InfluxDBServerError, InfluxDBClientError, RequestsConnectionError, Timeout) as e:
        logging.error(f"Failure writing to or reading from InfluxDB: {e}")
        db_client = database_connect(INFLUXDB_HOST, INFLUXDB_PORT, USERNAME, PASSWORD, DATABASE)

    time.sleep(5)
