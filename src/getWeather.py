"""
Get weather data from OpenWeather and write to InfluxDB.
"""

import os
import socket
import time
from datetime import datetime
from zoneinfo import ZoneInfo
from dotenv import load_dotenv
from requests import get
from influxdb import InfluxDBClient
from influxdb.exceptions import InfluxDBServerError

TRY_AGAIN_SECS = 60
GET_WEATHER_SLEEP_SECS = 600
TIME_ZONE = "America/Chicago"
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
                "tempHigh":               float(weatherData['daily'][0]['temp']['max']),
                "tempLow":                float(weatherData['daily'][0]['temp']['min']),
                "dailyCondition":         weatherData['daily'][0]['weather'][0]['main'],
                "dailyConditionTomorrow": weatherData['daily'][1]['weather'][0]['main'],
                "tempHighTomorrow":       int(weatherData['daily'][1]['temp']['max']),
                "tempLowTomorrow":        float(weatherData['daily'][1]['temp']['min']),
                "windDirection":          int(weatherData['current']['wind_deg']),
                "windSpeed":              float(weatherData['current']['wind_speed']),
                "windGust":               float(weatherData['daily'][0]['wind_gust']),
                "timeStamp": dateTimeNow
            },
            "time": dateTimeNow
        }

        print(point)
        series.append(point)
    except:
        print("Failure parsing weather data. Trying again in {TRY_AGAIN_SECS} seconds.")
        continue

    # GMT-5 (Summer), GMT-6 (Winter)
    now = datetime.now(ZoneInfo(TIME_ZONE))
    base_offset_seconds = (now.utcoffset() - now.dst()).total_seconds()
    dst_offset_seconds = now.dst().total_seconds()
    gmt_offset_seconds = base_offset_seconds + dst_offset_seconds
    GMT_OFFSET_MINUTES = str(int(gmt_offset_seconds / 60 * -1)) + 'm'

    try:
        client.write_points(series)
        print("Series written to InfluxDB.")
        query_result = client.query(f"SELECT * FROM weather WHERE time >= now() - {GMT_OFFSET_MINUTES} - 10m")
        print(f"Query results: {query_result}")
    except InfluxDBServerError as e:
        print("Failure writing to or reading from InfluxDB:", e)

    print(f"Sleeping for {GET_WEATHER_SLEEP_SECS / 60} minutes")
    time.sleep(GET_WEATHER_SLEEP_SECS)
