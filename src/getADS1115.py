"""
steve.a.mccluskey@gmail.com
Read Adafruit ADC (Analog-to-Digital Converter) breakout board and write to InfluxDB.
This uses the I2C (Inter-Integrated Circuit) protocol to get water pressure readings.
THIS FILE IS TO BE COMPLETELY REWRITTEN using JSON master config data. All channel variables have been removed from env template.
"""

import os
import socket
import time
import Adafruit_ADS1x15
from influxdb.exceptions import InfluxDBServerError
from dotenv import load_dotenv
from constants import PRESSURE_SENSOR_TYPE
from common_functions import database_connect

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
DATABASE = os.getenv("SENSOR_DATABASE")
PRESSURE_SENSOR_ID = os.getenv("PRESSURE_SENSOR_ID")

db_client = database_connect(INFLUXDB_HOST, INFLUXDB_PORT, USERNAME, PASSWORD, DATABASE)

print("Loading environment variables for all channels")

i2c_address0  = os.getenv("i2c_address")

channel0ID   = str(os.getenv("channel0ID"))
channel0name = str(os.getenv("channel0name"))
channel0     = int(os.getenv("channel0"))
ch0GAIN      = float(os.getenv("ch0GAIN"))
ch0maxPSI    = int(os.getenv("ch0maxPSI"))
ch0minPSI    = int(os.getenv("ch0minPSI"))
ch0minADC    = int(os.getenv("ch0minADC"))
ch0maxADC    = int(os.getenv("ch0maxADC"))
ch0enabled   = str(os.getenv("ch0enabled"))

channel1ID   = str(os.getenv("channel1ID"))
channel1name = str(os.getenv("channel1name"))
channel1     = int(os.getenv("channel1"))
ch1GAIN      = float(os.getenv("ch1GAIN"))
ch1maxPSI    = int(os.getenv("ch1maxPSI"))
ch1minPSI    = int(os.getenv("ch1minPSI"))
ch1minADC    = int(os.getenv("ch1minADC"))
ch1maxADC    = int(os.getenv("ch1maxADC"))
ch1enabled   = str(os.getenv("ch1enabled"))

channel2ID   = str(os.getenv("channel2ID"))
channel2name = str(os.getenv("channel2name"))
channel2     = int(os.getenv("channel2"))
ch2GAIN      = float(os.getenv("ch2GAIN"))
ch2maxPSI    = int(os.getenv("ch2maxPSI"))
ch2minPSI    = int(os.getenv("ch2minPSI"))
ch2minADC    = int(os.getenv("ch2minADC"))
ch2maxADC    = int(os.getenv("ch2maxADC"))
ch2enabled   = str(os.getenv("ch2enabled"))

channel3ID   = str(os.getenv("channel3ID"))
channel3name = str(os.getenv("channel3name"))
channel3     = int(os.getenv("channel3"))
ch3GAIN      = float(os.getenv("ch3GAIN"))
ch3maxPSI    = int(os.getenv("ch3maxPSI"))
ch3minPSI    = int(os.getenv("ch3minPSI"))
ch3minADC    = int(os.getenv("ch3minADC"))
ch3maxADC    = int(os.getenv("ch3maxADC"))
ch3enabled   = str(os.getenv("ch3enabled"))

adc = Adafruit_ADS1x15.ADS1115()

while True:
    print("Reading ADC:")
    series = []
    try:
        if ch0enabled == "Enabled":
            print("Reading channel " + str(channel0) + "...")
            #value0  = adc.read_adc(0, gain = 1)
            value0  = adc.read_adc(channel0, gain = ch0GAIN)
            #print(value0)
            psi0 = format((((value0 - ch0minADC) * (ch0maxPSI - ch0minPSI)) / (ch0maxADC - ch0minADC) + ch0minPSI), '.1f')
            if float(psi0) < 0.2:
                psi0 = str("Off")
            print (psi0, "   ", value0, "   ", channel0)
        else:
            psi0 = str("OFF")
            print(str(psi0) + ", channel " + str(channel0) + " disabled.")

        if ch1enabled == "Enabled":
            print("Reading channel " + str(channel1) + "...")
            value1 = adc.read_adc(channel1, gain = ch1GAIN)
            psi1 = format((((value1 - ch1minADC) * (ch1maxPSI - ch1minPSI)) / (ch1maxADC - ch1minADC) + ch1minPSI), '.1f')
            if float(psi1) < 0.2:
                psi1 = str("Off")
            print (psi1, "   ", value1, "   ", channel1)
        else:
            psi1 = str("OFF")
            print(str(psi1) + ", channel " + str(channel1) + " disabled.")

        if ch2enabled == "Enabled":
            print("Reading channel " + str(channel2) + "...")
            value2 = adc.read_adc(channel2, gain = ch2GAIN)
            psi2 = format((((value2 - ch2minADC) * (ch2maxPSI - ch2minPSI)) / (ch2maxADC - ch2minADC) + ch2minPSI), '.1f')
            if float(psi2) < 0.2:
                psi2 = str("Off")
            print (psi2, "   ", value2, "   ", channel2)
        else:
            psi2 = str("OFF")
            print(str(psi2) + ", channel " + str(channel2) + " disabled.")

        if ch3enabled == "Enabled":
            print("Reading channel " + str(channel3) + "...")
            value3 = adc.read_adc(channel3, gain = ch2GAIN)
            psi3 = format((((value3 - ch3minADC) * (ch3maxPSI - ch2minPSI)) / (ch3maxADC - ch3minADC) + ch3minPSI), '.1f')
            if float(psi3) < 0.2:
                psi3 = str("Off")
            print (psi3, "   ", value3, "   ", channel3)
        else:
            psi3 = str("OFF")
            print(str(psi3) + ", channel " + str(channel3) + " disabled.")

        #if (ch0enabled):
        point = {
            "measurement": "pressures",
            "tags": {
                "sensor":   0,
                "location": channel0ID,
                "title"   : channel0name,
                "id":       PRESSURE_SENSOR_ID,
                "channel":  channel0,
                "type":     PRESSURE_SENSOR_TYPE

            },
            "fields": {
                "pressure": psi0
            }
        }
        print(f"Point: {point}")
        series.append(point)

        point = {
            "measurement": "pressures",
            "tags": {
                "sensor":   1,
                "location": channel1ID,
                "title":    channel1name,
                "id":       PRESSURE_SENSOR_ID,
                "channel":  channel1,
                "type":     PRESSURE_SENSOR_TYPE
            },
            "fields": {
                "pressure": psi1
            }
        }
        print(f"Point: {point}")
        series.append(point)

        point = {
            "measurement": "pressures",
            "tags": {
                "sensor":   2,
                "location": channel2ID,
                "title":    channel2name,
                "id":       PRESSURE_SENSOR_ID,
                "channel":  channel2,
                "type":     PRESSURE_SENSOR_TYPE
            },
            "fields": {
                "pressure": psi2
            }
        }
        print(f"Point: {point}")
        series.append(point)

        point = {
            "measurement": "pressures",
            "tags": {
                "sensor":   3,
                "location": channel3ID,
                "title":    channel3name,
                "id":       PRESSURE_SENSOR_ID,
                "channel":  channel3,
                "type":     PRESSURE_SENSOR_TYPE
            },
            "fields": {
                "pressure": psi3
            }
        }
        print(f"Point: {point}")
        series.append(point)

    except:
        print("ADC not responding.")
        continue

    try:
        db_client.write_points(series)
        print("Series written to InfluxDB.")

        if DEBUG is True:
            query_result = db_client.query('SELECT * FROM "pressures" WHERE time >= now() - 5s')
            print(f"Query results: {query_result}")

    except InfluxDBServerError as e:
        print("Failure writing to or reading from InfluxDB:", e)

    time.sleep(5)
