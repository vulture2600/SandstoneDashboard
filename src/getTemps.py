"""
File to get master config file from NAS, read all 1-wire sensors, and post to InfluxDB.
This is a refactored version of the original getTemps.py script.
steve.a.mccluskey@gmail.com
"""

import datetime
import json
import os
import socket
import subprocess
import sys
import threading
import time
from os import path
from dotenv import load_dotenv
from influxdb import InfluxDBClient
from smb.SMBConnection import SMBConnection
from constants import DEVICES_PATH, W1_SLAVE_FILE, KERNEL_MOD_W1_GPIO, KERNEL_MOD_W1_THERM, TEMP_SENSOR_MODEL

DEBUG = True
RUN_CONTINUE = False # set to True to run continuously, False to run once and exit

HOSTNAME = socket.gethostname()

APP_ENV = os.getenv("APP_ENV")

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

MASTER_CONFIG_FILE = os.getenv("MASTER_CONFIG_FILE")
LOCAL_CONFIG_FILE = os.getenv('LOCAL_CONFIG_FILE')
SMB_SERVER = os.getenv("SMB_SERVER_IP")
SMB_SHARE = os.getenv("SMB_SHARE_NAME")
SMB_USER = os.getenv("SMB_USERNAME")
SMB_PASSWORD = os.getenv("SMB_PASSWORD")

DEGREE_SIGN = "\N{DEGREE SIGN}"

print("Verifying all kernel modules are loaded.")
kernel_mod_loads = []
kernel_mod_loads.append(subprocess.run(["modprobe", KERNEL_MOD_W1_GPIO], capture_output=True, text=True))
kernel_mod_loads.append(subprocess.run(["modprobe", KERNEL_MOD_W1_THERM], capture_output=True, text=True))

KERNEL_MOD_LOAD_FAIL = False

client = InfluxDBClient(INFLUXDB_HOST, INFLUXDB_PORT, USERNAME, PASSWORD, TEMP_SENSOR_DATABASE)
client.create_database(TEMP_SENSOR_DATABASE)
client.get_list_database()
client.switch_database(TEMP_SENSOR_DATABASE)
print("InfluxDB Client OK!")

for kernel_mod_load in kernel_mod_loads:
    if kernel_mod_load.returncode != 0:
        print(kernel_mod_load.stderr.rstrip())
        KERNEL_MOD_LOAD_FAIL = True

if KERNEL_MOD_LOAD_FAIL is True:
    print("Exiting")
    sys.exit(1)

## Delete read_temp() if it's no longer being used

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
        return "OFFLINE"


def multi_threaded_file_reader(file_paths):
    threads = []
    results = {}

    def read_file_thread(file_path):
        result = read_temp(file_path)
        results[file_path] = result

    for file_path in file_paths:
        thread = threading.Thread(target = read_file_thread, args = (file_path,))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()
    return results

#main loop here:
while True:
    #get config file from NAS:
    try:
        conn = SMBConnection(SMB_USER, SMB_PASSWORD, HOSTNAME, SMB_SERVER, use_ntlm_v2=True)
        connected = conn.connect(SMB_SERVER, 445) # Port 445 is standard for SMB

        if connected:
            if DEBUG is True:
                print(f"Successfully connected to {SMB_SERVER}!")

        with open(LOCAL_CONFIG_FILE, 'wb') as local_file:
        # Retrieve the remote file
            file_attributes, filesize = conn.retrieveFile(SMB_SHARE, MASTER_CONFIG_FILE, local_file)

        if DEBUG is True:
            print(f"File '{MASTER_CONFIG_FILE}' downloaded successfully to '{LOCAL_CONFIG_FILE}'")
        conn.close()
    except Exception as e:
        print(f"An error occurred: {e}. Attemping to use local config file instead.")

    try: #open local config file:
        with open(LOCAL_CONFIG_FILE, 'r') as CONFIG:
            CONFIG_JSON = json.load(CONFIG)

            if DEBUG is True:
                print("Config file loaded successfully.")
                print(type(CONFIG_JSON))
                print(CONFIG_JSON)
                print("")
    except:
        print("Config file not found.")
        sys.exit(1)

    try:
        one_wire_config = CONFIG_JSON['1-wire'] #get all 1-wire data
        if DEBUG is True:
            print("1-wire config data:")
            print(type(one_wire_config))
            print(one_wire_config)
            print("")

        rooms_ids = list(one_wire_config.keys()) # make list of room ids

        if DEBUG is True:
            print("List of Room IDs:")
            print(type(rooms_ids))
            print(rooms_ids)
            print("")

        found_rooms = {}

        for room in rooms_ids: #find all rooms that match this host name
            if one_wire_config[room].get('hostname') == HOSTNAME:
                new_room = {'id': one_wire_config[room].get('id'),
                            'hostname': one_wire_config[room].get('hostname'),
                            'title': one_wire_config[room].get('title')}
                found_rooms.update({room: new_room})

        if DEBUG is True:
            print("Config data matching this host's name:")
            print(type(found_rooms))
            print(found_rooms)
            print("")
    except:
        print("Getting rooms from config file failed!")

    #Read all sensors and post to InfluxDB
    try:
        rooms_ids = list(found_rooms.keys())
        if DEBUG is True:
            print("List of Room IDs after filtering by hostname:")
            print(type(rooms_ids))
            print(rooms_ids)
            print("")

        sensorIds = os.listdir(DEVICES_PATH) #all online sensors on bus
        series = []
        dateTimeNow = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if DEBUG is True:
            print("Found " + str((len(sensorIds) - 1)) +
                    " devices on bus: " +
                    datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            print(" ")

            print("Collecting temperatures from all sensors online...")

        results = multi_threaded_file_reader(sensorIds)

        i = 1
        for file_path, value in results.items(): #search all onlne sensors:
            if file_path.find('28-') != -1:
                if DEBUG is True:
                    print (str(i).zfill(2) + ") Sensor ID: "
                            + str(file_path) + ". Temp = "
                        + str(value) + DEGREE_SIGN + "F.")

                for room in rooms_ids: # check if sensor is in config file:
                    if found_rooms[room].get('id') == file_path:
                        point = {
                            "measurement": "raw_data",
                            "tags": {
                                "location:": room,
                                "sensor_id": file_path,
                                "title": found_rooms[room].get('title'),
                                "sensor_bus": "1-wire",
                                "hostname": HOSTNAME,
                                "type": TEMP_SENSOR_MODEL,
                                "timeStamp": dateTimeNow,
                                "status": "Online"
                            },
                            "fields": {
                                "temperature": float(value)
                            },
                        }
                        i += 1
                        if DEBUG is True:
                            print(point)
                            print(" ")
                        series.append(point)
                        break

                else:   #not found in config file, but still online.
                    point = {
                        "measurement": "raw_data",
                        "tags": {
                            "location:": "UNASSIGNED",
                            'title': "UNNAMED",
                            "sensor_id": file_path,
                            "sensor_bus": "1-wire",
                            "hostname": HOSTNAME,
                            "type": TEMP_SENSOR_MODEL,
                            "timeStamp": dateTimeNow,
                            "status": "Online"
                        },
                        "fields": {
                            "temperature": float(value)
                        },
                    }
                    if DEBUG is True:
                        print(point)
                        print(" ")
                    series.append(point)
                    i += 1

        for room in rooms_ids: #offline sensors in config file:
            if found_rooms[room].get('id') not in sensorIds:
                if DEBUG is True:
                    print(str(i).zfill(2) + ") Sensor ID: "
                        + found_rooms[room].get('id')
                        + " is OFFLINE!")

                point = {
                    "measurement": "raw_data",
                    "tags": {
                        "location:": room,
                        "sensor_id": found_rooms[room].get('id'),
                        "title": found_rooms[room].get('title'),
                        "sensor_bus": "1-wire",
                        "hostname": HOSTNAME,
                        "type": TEMP_SENSOR_MODEL,
                        "timeStamp": dateTimeNow,
                        "status": "OFFLINE"
                    },
                    "fields": {
                        "temperature": -100.0
                    },
                }
                if DEBUG is True:
                    print(point)
                    print(" ")
                series.append(point)
                i += 1


    except:
        print("Error reading sensors.")

    try:
        client.write_points(series)
        if DEBUG is True:
            print("Data posted to DB. " + dateTimeNow)
            print(" ")

        result = client.query('select * from "raw_data" where time >= now() - 1s and time <= now()')

        if DEBUG is True:
            print("Query recieved.")
            print(result)
            print(" ")

    except InfluxDBServerError as e:
        print("server failed, reason: " + str(e))
        print(" ")

    if RUN_CONTINUE is False:
        break

    time.sleep(2)
