"""
Get weather data from OpenWeather and write to InfluxDB.
"""

import os
import logging
import socket
import sys
import time
from datetime import datetime
from requests import get
from requests.exceptions import Timeout
from requests.exceptions import ConnectionError as RequestsConnectionError
from influxdb.exceptions import InfluxDBServerError, InfluxDBClientError
from common_functions import choose_dotenv, database_connect

TRY_AGAIN_SECS = 60
GET_WEATHER_SLEEP_SECS = 600
SLEEP_MINUTES = GET_WEATHER_SLEEP_SECS / 60
SLEEP_MINUTES_FORMATTED = f"{SLEEP_MINUTES:.1f}".rstrip("0").rstrip(".")
LOG_FILE = "/var/log/getWeather.log"

LOG_LEVEL = os.getenv("LOG_LEVEL_GET_WEATHER", "INFO").upper()
FORMAT = '%(asctime)-15s %(levelname)s %(message)s'
numeric_level = getattr(logging, LOG_LEVEL, logging.INFO)
logging.basicConfig(filename=LOG_FILE, level=numeric_level, format=FORMAT)
print(f"Logging to {LOG_FILE}")

logging.info(f"Python version: {sys.version}")
HOSTNAME = socket.gethostname()
choose_dotenv(HOSTNAME)

INFLUXDB_HOST = os.getenv("INFLUXDB_HOST")
INFLUXDB_PORT = os.getenv("INFLUXDB_PORT")
USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")
DATABASE = os.getenv("TEMP_SENSOR_DATABASE")
OPENWEATHERMAP_API_KEY = os.getenv("OPENWEATHERMAP_API_KEY")

LOCATION = os.getenv("LOCATION")
LATITUDE = os.getenv("LATITUDE")
LONGITUDE = os.getenv("LONGITUDE")

UNITS = 'imperial'

OPENWEATHERMAP_URL = (
    f"http://api.openweathermap.org/data/3.0/onecall"
    f"?lat={LATITUDE}"
    f"&lon={LONGITUDE}"
    f"&exclude=minutely,hourly"
    f"&appid={OPENWEATHERMAP_API_KEY}"
    f"&units={UNITS}"
)

db_client = database_connect(INFLUXDB_HOST, INFLUXDB_PORT, USERNAME, PASSWORD, DATABASE)

while True:
    try:
        weatherData = get(OPENWEATHERMAP_URL, timeout=5).json()
    except Exception as e:
        logging.error(f"Failed to get weather data: {e}")
        logging.error(f"Trying again in {TRY_AGAIN_SECS} seconds...")
        time.sleep(TRY_AGAIN_SECS)
        continue

    series = []
    TODAY, TOMORROW = 0, 1
    dateTimeNow = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        point = {
            "measurement": "weather",
            "tags": {
                "location": LOCATION
            },
            "fields": {
                "humidity":               int(weatherData['current']['humidity']),
                "feelsLike":              float(weatherData['current']['feels_like']),
                "currentCondition":       weatherData['current']['weather'][0]['main'],
                "tempHigh":               float(weatherData['daily'][TODAY]['temp']['max']),
                "tempLow":                float(weatherData['daily'][TODAY]['temp']['min']),
                "dailyCondition":         weatherData['daily'][TODAY]['weather'][0]['main'],
                "dailyConditionTomorrow": weatherData['daily'][TOMORROW]['weather'][0]['main'],
                "tempHighTomorrow":       int(weatherData['daily'][TOMORROW]['temp']['max']),
                "tempLowTomorrow":        float(weatherData['daily'][TOMORROW]['temp']['min']),
                "windDirection":          int(weatherData['current']['wind_deg']),
                "windSpeed":              float(weatherData['current']['wind_speed']),
                "windGust":               float(weatherData['daily'][TODAY]['wind_gust']),
                "timeStamp": dateTimeNow
            }
        }
        logging.debug(f"Point: {point}")
        series.append(point)

    except Exception as e:
        logging.error(f"Failure parsing weather data: {e}")
        logging.error(f"Trying again in {TRY_AGAIN_SECS} seconds...")
        time.sleep(TRY_AGAIN_SECS)
        continue

    try:
        db_client.write_points(series)
        logging.info("Series written to InfluxDB.")

        if LOG_LEVEL == 'DEBUG':
            query_result = db_client.query('SELECT * FROM "weather" WHERE time >= now() - 10m')
            logging.debug(f"Query results: {query_result}")

    except (InfluxDBServerError, InfluxDBClientError, RequestsConnectionError, Timeout) as e:
        logging.error(f"Failure writing to or reading from InfluxDB: {e}")
        db_client = database_connect(INFLUXDB_HOST, INFLUXDB_PORT, USERNAME, PASSWORD, DATABASE)

    logging.info(f"Sleeping for {SLEEP_MINUTES_FORMATTED} minutes...")
    time.sleep(GET_WEATHER_SLEEP_SECS)
