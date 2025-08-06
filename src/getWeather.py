"""
Get weather data from OpenWeather and write to InfluxDB.
"""

import os
import socket
import time
from datetime import datetime
from dotenv import load_dotenv
from requests import get
from influxdb import InfluxDBClient
from influxdb.exceptions import InfluxDBServerError

DEBUG = False  # set to True to print query result

TRY_AGAIN_SECS = 60
GET_WEATHER_SLEEP_SECS = 600
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
TEMP_SENSOR_DATABASE = os.getenv("TEMP_SENSOR_DATABASE")
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

print("Connecting to the database")
client = InfluxDBClient(INFLUXDB_HOST, INFLUXDB_PORT, USERNAME, PASSWORD, TEMP_SENSOR_DATABASE)
databases = client.get_list_database()
if not any(db['name'] == TEMP_SENSOR_DATABASE for db in databases):
    print(f"Creating {TEMP_SENSOR_DATABASE}")
    client.create_database(TEMP_SENSOR_DATABASE)
    client.switch_database(TEMP_SENSOR_DATABASE)
print(f"InfluxDB client ok! Using {TEMP_SENSOR_DATABASE}")

while True:
    try:
        weatherData = get(OPENWEATHERMAP_URL, timeout=5).json()
    except:
        print(f"Failed to get weather data. Trying again in {TRY_AGAIN_SECS} seconds.")
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

    except:
        print("Failure parsing weather data. Trying again in {TRY_AGAIN_SECS} seconds.")
        continue

    try:
        client.write_points(series)
        print("Series written to InfluxDB.")

        if DEBUG is True:
            query_result = client.query('SELECT * FROM "weather" WHERE time >= now() - 10m')
            print(f"Query results: {query_result}")

    except InfluxDBServerError as e:
        print("Failure writing to or reading from InfluxDB:", e)

    SLEEP_MINUTES = GET_WEATHER_SLEEP_SECS / 60
    SLEEP_MINUTES_FORMATTED = f"{SLEEP_MINUTES:.1f}".rstrip("0").rstrip(".")

    print(f"Sleeping for {SLEEP_MINUTES_FORMATTED} minutes")
    time.sleep(GET_WEATHER_SLEEP_SECS)
