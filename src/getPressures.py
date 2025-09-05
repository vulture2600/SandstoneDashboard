"""
Read Adafruit ADC (Analog-to-Digital Converter) breakout board and write to InfluxDB.
This uses the I2C (Inter-Integrated Circuit) protocol to get water pressure readings.
Developers: steve.a.mccluskey@gmail.com, see repo for others.
"""

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
from common_functions import choose_dotenv, database_connect, SMBFileTransfer, load_json_file

CONFIG_FILE_TRY_AGAIN_SECS = 60
CONFIG_FILE_NAME = "getPressures.json"
CONFIG_FILE = f"config/{CONFIG_FILE_NAME}"

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

PRESSURE_SENSOR_ID = "i2c:0x48"
I2C_ADDR = int(PRESSURE_SENSOR_ID.split(':')[1], 16)

adc = Adafruit_ADS1x15.ADS1115(address=I2C_ADDR, busnum=1)

while True:

    logging.info(f"Updating {CONFIG_FILE_NAME} if old or missing")
    GET_JSON_SUCCESSFUL = smb_client.get_json_config()

    logging.info(f"Loading {CONFIG_FILE_NAME}")
    json_config = load_json_file(CONFIG_FILE)

    if json_config is None:
        logging.warning(f"Trying again in {CONFIG_FILE_TRY_AGAIN_SECS} seconds")
        time.sleep(CONFIG_FILE_TRY_AGAIN_SECS)
        continue

    CHANNELS = json_config.get(HOSTNAME)

    if CHANNELS is None:
        logging.warning(f"Hostname not found in {CONFIG_FILE_NAME}")
        logging.warning(f"Trying again in {CONFIG_FILE_TRY_AGAIN_SECS} seconds")
        time.sleep(CONFIG_FILE_TRY_AGAIN_SECS)
        continue

    if not CHANNELS:
        logging.warning(f"No sensors for {HOSTNAME} found in {CONFIG_FILE_NAME}")
        logging.warning(f"Trying again in {CONFIG_FILE_TRY_AGAIN_SECS} seconds")
        time.sleep(CONFIG_FILE_TRY_AGAIN_SECS)
        continue

    channel_count = len(CHANNELS)
    logging.debug(f"Channels in {CONFIG_FILE_NAME}: {CHANNELS}")

    logging.info("Reading ADC:")
    series = []
    try:
        ch0 = CHANNELS["channel0"]
        if ch0["ch0enabled"] == "Enabled":
            logging.info(f"Reading channel {ch0['channel0']}...")
            value0  = adc.read_adc(ch0["channel0"], gain = ch0["ch0GAIN"])
            psi0 = format((((value0 - ch0["ch0minADC"]) * (ch0["ch0maxPSI"] - ch0["ch0minPSI"])) / (ch0["ch0maxADC"] - ch0["ch0minADC"]) + ch0["ch0minPSI"]), '.1f')
            if float(psi0) < 0.2:
                psi0 = "Off"
            logging.info(f"{psi0} {value0} {ch0['channel0']}")
        else:
            psi0 = "OFF"
            logging.info(f"{psi0}, channel {ch0['channel0']} disabled.")

        ch1 = CHANNELS["channel1"]
        if ch1["ch1enabled"] == "Enabled":
            logging.info(f"Reading channel {ch1['channel1']}...")
            value1 = adc.read_adc(ch1["channel1"], gain = ch1["ch1GAIN"])
            psi1 = format((((value1 - ch1["ch1minADC"]) * (ch1["ch1maxPSI"] - ch1["ch1minPSI"])) / (ch1["ch1maxADC"] - ch1["ch1minADC"]) + ch1["ch1minPSI"]), '.1f')
            if float(psi1) < 0.2:
                psi1 = "Off"
            logging.info(f"{psi1} {value1} {ch1['channel1']}")
        else:
            psi1 = "OFF"
            logging.info(f"{psi1}, channel {ch1['channel1']} disabled.")

        ch2 = CHANNELS["channel2"]
        if ch2["ch2enabled"] == "Enabled":
            logging.info(f"Reading channel {ch2['channel2']}...")
            value2 = adc.read_adc(ch2["channel2"], gain = ch2["ch2GAIN"])
            psi2 = format((((value2 - ch2["ch2minADC"]) * (ch2["ch2maxPSI"] - ch2["ch2minPSI"])) / (ch2["ch2maxADC"] - ch2["ch2minADC"]) + ch2["ch2minPSI"]), '.1f')
            if float(psi2) < 0.2:
                psi2 = "Off"
            logging.info(f"{psi2} {value2} {ch2['channel2']}")
        else:
            psi2 = "OFF"
            logging.info(f"{psi2}, channel {ch2['channel2']} disabled.")

        ch3 = CHANNELS["channel3"]
        if ch3["ch3enabled"] == "Enabled":
            logging.info(f"Reading channel {ch3['channel3']}...")
            value3 = adc.read_adc(ch3["channel3"], gain = ch3["ch2GAIN"])
            psi3 = format((((value3 - ch3["ch3minADC"]) * (ch3["ch3maxPSI"] - ch3["ch2minPSI"])) / (ch3["ch3maxADC"] - ch3["ch3minADC"]) + ch3["ch3minPSI"]), '.1f')
            if float(psi3) < 0.2:
                psi3 = "Off"
            logging.info(f"{psi3} {value3} {ch3['channel3']}")
        else:
            psi3 = "OFF"
            logging.info(f"{psi3}, channel {ch3['channel3']} disabled.")

        point = {
            "measurement": "pressures",
            "tags": {
                "sensor":   0,
                "location": ch0["channel0ID"],
                "title":    ch0["channel0name"],
                "id":       PRESSURE_SENSOR_ID,
                "channel":  ch0["channel0"],
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
                "location": ch1["channel1ID"],
                "title":    ch1["channel1name"],
                "id":       PRESSURE_SENSOR_ID,
                "channel":  ch1["channel1"],
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
                "location": ch2["channel2ID"],
                "title":    ch2["channel2name"],
                "id":       PRESSURE_SENSOR_ID,
                "channel":  ch2["channel2"],
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
                "location": ch3["channel3ID"],
                "title":    ch3["channel3name"],
                "id":       PRESSURE_SENSOR_ID,
                "channel":  ch3["channel3"],
                "type":     PRESSURE_SENSOR_TYPE,
                "hostname": HOSTNAME
            },
            "fields": {
                "pressure": psi3
            }
        }
        logging.debug(f"Point: {point}")
        series.append(point)

    except Exception as e:
        logging.error(f"ADC not responding. {e}")
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
