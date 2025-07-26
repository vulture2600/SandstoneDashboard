"""
test file to read all 1-wire temp folders and post their current temps to database

adding SMB functionality to read a config file on NAS
and save it locally.

"""



import os
import time
import datetime
from os import path
import threading
from influxdb import InfluxDBClient
from constants import DEVICES_PATH, W1_SLAVE_FILE
import shutil
from dotenv import load_dotenv
from smb.SMBConnection import SMBConnection
import socket
import json



DEBUG = True
RUN_CONTINUE = False #set to True to run continuously, False to run once and exit

APP_ENV = os.getenv("APP_ENV")

if APP_ENV is None:
    print("APP_ENV not set, using .env file")
    load_dotenv(override=True)
else:
    print(f"Using .env.{APP_ENV} file")
    load_dotenv(override=True, dotenv_path=f".env.{APP_ENV}")

INFLUXDB_HOST = os.getenv("INFLUXDB_HOST")
INFLUXDB_PORT = os.getenv("INFLUXDB_PORT")
USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")
TEMP_SENSOR_DATABASE = os.getenv("SENSOR_DATABASE")
CONFIG_FILE = os.getenv("CONFIG_FILE")

SMB_SERVER = os.getenv("SMB_SERVER_IP")
SMB_SHARE = os.getenv("SMB_SHARE_NAME")
SMB_USER = os.getenv("SMB_USERNAME")
SMB_PASSWORD = os.getenv("SMB_PASSWORD")

local_save_path = 'config.json'

os.system('modprobe w1-gpio')
os.system('modprobe w1-therm')

degree_sign = u"\N{DEGREE SIGN}"

hostname = socket.gethostname()

client = InfluxDBClient(INFLUXDB_HOST, INFLUXDB_PORT, USERNAME, PASSWORD, TEMP_SENSOR_DATABASE)
client.create_database(TEMP_SENSOR_DATABASE)
client.get_list_database()
client.switch_database(TEMP_SENSOR_DATABASE)
print("InfluxDB Client OK!")


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

#reads /temperature file
def read_temp_f(file):
    device_file = DEVICES_PATH + file + "/temperature"

    if (path.exists(device_file)):
        try:
            f = open (device_file, 'r')
            temp_string = f.read()
#			f.close()

            temp_c = float(temp_string) / 1000.0
            temp_f = temp_c * 1.8 + 32.0
            return format(temp_f, '.1f')
        except:
            return "OFF"
    else:
        return "OFFLINE"




def multi_threaded_file_reader(file_paths):
    threads = []
    results = {}

    def read_file_thread(file_path):
        result = read_temp_f(file_path)
        results[file_path] = result

    for file_path in file_paths:
        thread = threading.Thread(target = read_file_thread, args = (file_path,))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    return results





while True:
    #get config file from NAS:
    try:
        conn = SMBConnection(SMB_USER, SMB_PASSWORD, hostname, SMB_SERVER, use_ntlm_v2=True)
        connected = conn.connect(SMB_SERVER, 445) # Port 445 is standard for SMB
    
        if connected:
            print(f"Successfully connected to {SMB_SERVER}!")
    
        with open(local_save_path, 'wb') as local_file:
        # Retrieve the remote file
            file_attributes, filesize = conn.retrieveFile(SMB_SHARE, CONFIG_FILE, local_file)

        print(f"File '{CONFIG_FILE}' downloaded successfully to '{local_save_path}'")
        conn.close()
    except Exception as e:
        print(f"An error occurred: {e}")


    try: #open config file:
        with open(local_save_path, 'r') as CONFIG:
            config_data = CONFIG.read()
            CONFIG_JSON = json.loads(config_data)
            print(CONFIG_JSON)
    except:
        print("Config file not found.")


    #Read all sensors and post to InfluxDB
    try:
        print("Reading Sensors:")
        sensorIds = os.listdir(DEVICES_PATH)
#       print(sensorIds)
        series = []
        dateTimeNow = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        print("Found " + str((len(sensorIds) - 1)) + " devices on bus: " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        print("Collecting temperatures ...")
        i = 1
        results = multi_threaded_file_reader(sensorIds)

        for file_path, content in results.items():
            if (file_path.find('28-') != -1):
                print (str(i).zfill(2) + ") Sensor ID: " + str(file_path) + ". Temp = " + str(content) + degree_sign + "F.")
                i += 1
                point = {
                    "measurement": "raw_data",
                    "tags": {
                        "sensor_id": file_path,
                        "sensor_bus": "1-wire",
                        "hostname": hostname,
                        "type": "ds18b20",
                        "timeStamp": dateTimeNow

                    },
                    "fields": {
                        "temperature": float(content)
                    },
                }
                series.append(point)

        if DEBUG is True:
            print("Series to post: ")
            print(series)

    except:        
        print("Error reading sensors.")            

    print(" ")

    try:
        client.write_points(series)
        print("Data posted to DB.")

        result = client.query('select * from "raw_data" where time >= now() - 1s and time <= now()')
        print("Query recieved.")
        if DEBUG is True:
            print(result)
        print(" ")
    except InfluxDBServerError as e:
        # print("Server timeout")
        print("server failed, reason: " + str(e))
        print(" ")

    time.sleep(2)

    if RUN_CONTINUE is False:
        break


    time.sleep(2)