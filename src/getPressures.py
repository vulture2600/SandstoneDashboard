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

PRESSURE_SENSOR_ID = "i2c:0x48"
I2C_ADDR = int(PRESSURE_SENSOR_ID.split(':')[1], 16)
PSI_LOWER_BOUND = 0.2
NO_PSI = -999.9

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

ADC = Adafruit_ADS1x15.ADS1115(address=I2C_ADDR, busnum=1)

class PressureSensorReader:
    """Read attached pressure sensors"""
    def __init__(self, adc, channels, hostname, sensor_id, sensor_type):
        """
        adc        -> ADC device instance
        channels   -> dict of channel configs (from JSON)
        hostname   -> string, host name
        sensor_id  -> string, sensor id (like i2c:0x48)
        sensor_type-> string, sensor type
        """
        self.adc = adc
        self.channels = channels
        self.hostname = hostname
        self.sensor_id = sensor_id
        self.sensor_type = sensor_type

    def read_channels(self):
        """
        Read all enabled channels in config.
        Return {channel: psi_float or NO_PSI}
        Example: {'channel0': 4.8, 'channel1': NO_PSI}
        """
        results = {}

        for channel, ch_cfg in self.channels.items():
            results[channel] = NO_PSI

            try:
                ch_num = ch_cfg["channel"]

                if ch_cfg.get("ch_enabled") != "Enabled":
                    logging.info(f"Channel {ch_num} disabled")
                    continue

                logging.info(f"Reading channel {ch_num}...")

                value = self.adc.read_adc(ch_num, gain=ch_cfg["ch_gain"])

                psi = (
                    (float(value) - ch_cfg["ch_minADC"]) *
                    (ch_cfg["ch_maxPSI"] - ch_cfg["ch_minPSI"]) /
                    (ch_cfg["ch_maxADC"] - ch_cfg["ch_minADC"]) +
                    ch_cfg["ch_minPSI"]
                )
                psi_str = f"{psi:.1f}"
                if psi < PSI_LOWER_BOUND:
                    psi_str = "OFF"

                logging.info(f"Channel {ch_num}, ADC {value}, PSI {psi_str}")
                results[channel] = psi

            except Exception as e:
                logging.error(f"Error reading {channel}: {e}")

        return results

    def construct_points(self, readings):
        """Construct points for InfluxDB from readings. Return series."""

        series = []
        for channel, psi in readings.items():
            psi_str = f"{psi:.1f}"
            if psi < PSI_LOWER_BOUND:
                psi_str = "OFF"

            ch_cfg = self.channels[channel]
            point = {
                "measurement": "pressures",
                "tags": {
                    "location": ch_cfg["channel_ID"],
                    "title": ch_cfg["channel_name"],
                    "id": self.sensor_id,
                    "channel": ch_cfg["channel"],
                    "type": self.sensor_type,
                    "hostname": self.hostname,
                },
                "fields": {
                    "pressure": psi_str,
                    "pressure_flt": psi
                },
            }
            logging.debug(f"Point: {point}")
            series.append(point)
        return series

try:
    while True:

        logging.info(f"Updating {CONFIG_FILE_NAME} if missing or old")
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

        logging.info("Reading ADC")

        pressure_sensor_reader = PressureSensorReader(
            adc=ADC,
            channels=CHANNELS,
            hostname=HOSTNAME,
            sensor_id=PRESSURE_SENSOR_ID,
            sensor_type=PRESSURE_SENSOR_TYPE,
        )

        PRESSURE_READINGS = pressure_sensor_reader.read_channels()
        SERIES = pressure_sensor_reader.construct_points(PRESSURE_READINGS)

        try:
            db_client.write_points(SERIES)
            logging.info("Series written to InfluxDB.")

            if LOG_LEVEL == 'DEBUG':
                query_result = db_client.query('SELECT * FROM "pressures" WHERE time >= now() - 5s')
                logging.debug(f"Query results: {query_result}")

        except (InfluxDBServerError, InfluxDBClientError, RequestsConnectionError, Timeout) as e:
            logging.error(f"Failure writing to or reading from InfluxDB: {e}")
            db_client = database_connect(INFLUXDB_HOST, INFLUXDB_PORT, USERNAME, PASSWORD, DATABASE)

        time.sleep(5)

except KeyboardInterrupt:
    logging.info("Exiting gracefully")
    print()
finally:
    db_client.close()
