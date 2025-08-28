# SandstoneDashboard Python files

### Python virtual environment

Activate/deactivate

```shell
# If the directory has a .venv symlink, try using the 'activate' alias instead of the source command.

cd ~/SandstoneDashboard  # or any directory with a venv
source venv/bin/activate

deactivate
```

Install Python packages from [requirements.txt](../requirements.txt)

```shell
# Make sure the virtual environment is activated.

pip install --upgrade pip setuptools  # nice, but not required

pip install -r requirements.txt

pip check  # check for broken requirements
```

### Dotenv

The dotenv file containing values specific to the host is chosen based on whether the Python script was started by systemd or without. See the choose_dotenv function in [common_functions.py](common_functions.py)

### Logging

```shell
tail -f /var/log/SandstoneDashboard/getPressures.log
tail -f /var/log/SandstoneDashboard/getSHT30.log
tail -f /var/log/SandstoneDashboard/getTemps.log
tail -f /var/log/SandstoneDashboard/getWeather.log
```

Or use the symlinks to each log file in /var/log

### Sensor config files

* json files containing sensor ids and locations are pulled from an SMB share each time temperature, humidity, and eventually pressure values are read. This makes the sensors "hot swappable."
* Sensors not found in the config files will be read and the data point will be sent to InfluxDB with the location tag set to 'unassigned'.
* These unassigned sensors will show as untitled and unassigned in Grafana.
* The top level keys in the json examples below are host names.


#### Format

getSHT30.json

```json
{
    "SandstoneShed1": {
        "shedSHT30": {
            "id": "i2c:0x44",
            "title": "Shed SHT30"
        }
    }
}
```

getTemps.json

```json
{
    "SandstoneSchoolRoom1": {
        "UpSchlRmOutsideTemp": {
            "id": "28-000000833db4",
            "title": "Upper School Room Outside Temp"
        }
    }
}
```
