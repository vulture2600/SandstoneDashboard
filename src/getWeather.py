"""
Get weather data from OpenWeather and write to InfluxDB.
"""

import os
import socket
import time
from datetime import datetime
from dotenv import load_dotenv
from requests import get
from requests.exceptions import Timeout
from requests.exceptions import ConnectionError as RequestsConnectionError
from influxdb.exceptions import InfluxDBServerError, InfluxDBClientError
from common_functions import database_connect

DEBUG = False  # set to True to print query result

HOSTNAME = socket.gethostname()
TRY_AGAIN_SECS = 60
GET_WEATHER_SLEEP_SECS = 600
SLEEP_MINUTES = GET_WEATHER_SLEEP_SECS / 60
SLEEP_MINUTES_FORMATTED = f"{SLEEP_MINUTES:.1f}".rstrip("0").rstrip(".")

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
        print(f"Failed to get weather data: {e}")
        print(f"Trying again in {TRY_AGAIN_SECS} seconds...")
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
        print(f"Point: {point}")
        series.append(point)

    except Exception as e:
        print(f"Failure parsing weather data: {e}")
        print(f"Trying again in {TRY_AGAIN_SECS} seconds...")
        time.sleep(TRY_AGAIN_SECS)
        continue

    try:
        db_client.write_points(series)
        print("Series written to InfluxDB.")

        if DEBUG is True:
            query_result = db_client.query('SELECT * FROM "weather" WHERE time >= now() - 10m')
            print(f"Query results: {query_result}")

    except (InfluxDBServerError, InfluxDBClientError, RequestsConnectionError, Timeout) as e:
        print(f"Failure writing to or reading from InfluxDB: {e}")
        db_client = database_connect(INFLUXDB_HOST, INFLUXDB_PORT, USERNAME, PASSWORD, DATABASE)

    print(f"Sleeping for {SLEEP_MINUTES_FORMATTED} minutes...")
    time.sleep(GET_WEATHER_SLEEP_SECS)
