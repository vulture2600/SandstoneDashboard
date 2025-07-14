"""
test file to read all 1-wire temp folders and post their current temps to database



"""



import os
import time
import datetime
from os import path
import threading
from influxdb import InfluxDBClient
from constants import DEVICES_PATH, W1_SLAVE_FILE


from dotenv import load_dotenv

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

os.system('modprobe w1-gpio')
os.system('modprobe w1-therm')

degree_sign = u"\N{DEGREE SIGN}"

import socket

hostname = socket.gethostname()


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
        return "OFFLINE"
    
#reads /temperature file
def read_temp_f(file):
    device_file = DEVICES_PATH + file + "/temperature"
    #print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    if (path.exists(device_file)):
#		print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
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
    try:
        print("Reading Sensors:")
        sensorIds = os.listdir(DEVICES_PATH)
        print(sensorIds)
        series = []
        dateTimeNow = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")




        print("Found " + str((len(sensorIds) - 1)) + " devices on bus: " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        print("Collecting temperatures ...")
        i = 1
        results = multi_threaded_file_reader(sensorIds)

        for file_path, content in results.items():
            if (file_path.find('28-') != -1):
                print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
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
        #point = {
         #   "measurement": "raw_data",
          #  "tags": {
           #     "time_now" : "mostRecent"
            #},
            #"fields": {
            #    "timeStamp": dateTimeNow
            #}
        
        #}
        series.append(point)
        #print(series)
        client.write_points(series)
        print("Data written to InfluxDB: " + str(series))



    except:        print("Error reading sensors or writing to InfluxDB.")            



    print(" ")
    try:
        client.write_points(series)
        print("Data posted to DB.")

        result = client.query('select * from "raw_data" where time >= now() - 1s and time <= now()')
        print(result)
        print("Query recieved.")
        print(" ")
    except InfluxDBServerError as e:
        # print("Server timeout")
        print("server failed, reason: " + str(e))
        print(" ")

    time.sleep(2)

