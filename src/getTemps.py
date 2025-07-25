"""
steve.a.mccluskey@gmail.com
Get temp sensor data and write to InfluxDB. See .env files for required config file.
"""

import ast
import datetime
import os
import socket
from os import path
from dotenv import load_dotenv
from influxdb import InfluxDBClient
from constants import DEVICES_PATH, W1_SLAVE_FILE

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
TEMP_SENSOR_DATABASE = os.getenv("SENSOR_DATABASE")
CONFIG_FILE = os.getenv("CONFIG_FILE")

os.system('modprobe w1-gpio')
os.system('modprobe w1-therm')

client = InfluxDBClient(INFLUXDB_HOST, INFLUXDB_PORT, USERNAME, PASSWORD, TEMP_SENSOR_DATABASE)
client.create_database(TEMP_SENSOR_DATABASE)
client.get_list_database()
client.switch_database(TEMP_SENSOR_DATABASE)
print("client ok!")


def read_temp(file) -> str:
    device_file = DEVICES_PATH + file + "/" + W1_SLAVE_FILE
    if path.exists(device_file):
        try:
            f = open(device_file, 'r')
            lines = f.readlines()
            f.close()

            position = lines[1].find('t=')

            if position != -1:
                temp_string = lines[1][position + 2:]
                temp_c 		= float(temp_string) / 1000.0
                temp_f 		= format((temp_c * 1.8 + 32.0), '.1f')
                return temp_f
        except:
            return "Off"
    else:
        return "Off"


def key_exists(roomID, keys) -> bool:
    if keys and roomID:
        return key_exists(roomID.get(keys[0]), keys[1:])
    return not keys and roomID is not None


while True:
    print("Reading Sensors:")
    series = []
    dateTimeNow = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(CONFIG_FILE) as f:
        ROOMS = f.read()
    ROOMS = ast.literal_eval(ROOMS)

    # get number of rooms from config file and make arrays:
    count = len(ROOMS)

    for i in range(count):
        try:
            room_id = list(ROOMS.keys())[i]
            if key_exists(ROOMS, [room_id, 'id']):
                sensor_id = ROOMS.get(room_id, {}).get('id')
                temp 	  = read_temp(sensor_id)
                status = "On"
            else:
                sensor_id = "unassigned"
                temp 	  = "Off"
                # temp 	  = -100.0
                # status = "Off"

            if key_exists(ROOMS, [room_id, 'title']):
                title = ROOMS.get(room_id, {}).get('title')
            else:
                title = "Untitled"
            room_id_in_quotes = str("'" + room_id + "'")
            title_in_quotes   = str("'" + title + "'")

            print(
                "Sensor " + str(i + 1).zfill(2) + ") collected. " +
                "Room ID: " + str(room_id_in_quotes).ljust(21, ' ') +
                "Title: " + str(title_in_quotes).ljust(29, ' ') +
                "Sensor ID: " + str(sensor_id).center(15, '-') +
                ", Temp = " + str(temp) + "F"
            )

            if temp == "Off":
                # print(f"temp is {temp}, skipping room {room_id}")
                # continue
                status = "Off"
                # temp = -100.0

            point = {
                "measurement": "temps",
                "tags": {
                    "sensor": 	i + 1,
                    "location": room_id,
                    "id": 		sensor_id,
                    "type": 	"ds18b20",
                    "title": 	title
                },

                "fields": {
                    "status":       str(status),
                    "temp_flt": 	float(temp)
                }
            }

            series.append(point)

        except:
            i = i + 1

    point = {
        "measurement": "temps",
        "tags": {
            "TempSensorData" : "mostRecent"
        },
        "fields": {
            "timeStamp": dateTimeNow
        }
    }
    series.append(point)
    print(str(i + 1) + " sensors collected.")
    print(series)

    try:
        client.write_points(series)
        print("Data posted to DB.")

        result = client.query('select * from "temps" where time >= now() - 5s and time <= now()')
        print(result)
        print("Query recieved.")
        print(" ")
    except InfluxDBServerError as e:
        # print("Server timeout")
        print("server failed, reason: " + str(e))
        print(" ")
