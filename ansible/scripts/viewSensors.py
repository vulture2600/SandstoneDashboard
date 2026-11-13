"""
Utility to display all available OneWire temp sensors on the bus.
Developers: steve.a.mccluskey@gmail.com, see repo for others.
"""

import os
import datetime
import subprocess
import threading
import time

DEVICES_PATH = "/sys/bus/w1/devices/"
TEMP_SENSOR_ID_PREFIX = "28-"
DEGREE_SIGN_F = "\N{DEGREE SIGN}F"


def read_temp(file: str) -> str:
    """Reads temperature file"""

    device_file = DEVICES_PATH + file + "/temperature"

    try:
        with open(device_file, "r") as f:
            temp_string = f.read()

        temp_c = float(temp_string) / 1000.0
        temp_f = str(round(temp_c * 1.8 + 32, 1)) + DEGREE_SIGN_F
        return temp_f

    except FileNotFoundError as e:
        print(f"File not found: {device_file} — {e}")
        return "OFF"
    except ValueError as e:
        print(f"Error parsing temperature value: {e}")
        return "OFF"
    except Exception as e:
        print(f"Unexpected error: {e}")
        return "OFF"

def multi_threaded_file_reader(file_paths):
    """Creates a thread for each file path to read temperature concurrently."""
    threads = []
    results = {}

    def read_file_thread(file_path):
        """Reads the temperature from a file and stores the result in the results dictionary."""
        result = read_temp(file_path)
        results[file_path] = result

    for file_path in file_paths:
        thread = threading.Thread(target = read_file_thread, args = (file_path,))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    return results

if __name__ == "__main__":

    # Verify kernel modules are loaded:
    subprocess.run(["modprobe", "w1-gpio"], check=True)
    subprocess.run(["modprobe", "w1-therm"], check=True)

    try:
        while True:

            sensor_ids = os.listdir(DEVICES_PATH)
            sensor_ids = [sensor_id for sensor_id in sensor_ids if sensor_id.startswith(TEMP_SENSOR_ID_PREFIX)]

            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"Found {len(sensor_ids)} devices on 1-Wire bus, {timestamp}")
            print("Collecting temperatures...")

            multi_results = multi_threaded_file_reader(sensor_ids)

            for i, (sensor_id, temp) in enumerate(multi_results.items(), start=1):
                print(f"{str(i).zfill(2)}) Sensor ID: {sensor_id}, Temp = {temp}")

            print()
            time.sleep(2)

    except KeyboardInterrupt:
        print(" Exiting...\n")
