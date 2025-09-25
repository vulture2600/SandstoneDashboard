# SandstoneDashboard Python files

### Python virtual environment

Activate/deactivate

```shell
cd ~/src             # or wherever the code is deployed
python -m venv venv  # if the venv hasn't been created
source venv/bin/activate

deactivate
```

Install Python packages from [requirements.txt](requirements.txt)

```shell
# Make sure the virtual environment is activated.

pip install --upgrade pip setuptools  # nice, but not required

pip install -r requirements.txt

pip check  # check for broken requirements
```

### Dotenv

See [.env.template](.env.template) and the choose_dotenv function in [common_functions.py](common_functions.py)

### Logging

The log file path is set in the [dotenv](.env.template) file.

 Follow any of the log files directly or use the symlinks to each log file in /var/log.

```shell
tail -f /var/log/SandstoneDashboard/getPressures.log
tail -f /var/log/SandstoneDashboard/getSHT30.log
tail -f /var/log/SandstoneDashboard/getTemps.log
tail -f /var/log/SandstoneDashboard/getWeather.log
```

### Sensor config files

* json files containing sensor ids and locations are read from /config.
* If the json file is missing or older than the remote copy, the remote copy is pulled from an SMB share each time temperature, humidity, and eventually pressure values are read. This makes the sensors "hot swappable."
* The local json file (new or old) is read whether or not the remote copy is accessible.
* Sensors not found in the config files will be read and the data point will be sent to InfluxDB with the location tag set to 'unassigned'.
* These unassigned sensors will show as untitled and unassigned in Grafana.
* The top level keys in the json examples below are host names.


#### Format

getPressures.json

```json
{
    "SandstoneShed1": {
        "channel0": {
            "channel_ID": "schoolRoomDump",
            "channel_name": "School Room Dump Pressure",
            "channel": 0,
            "ch_gain": 1.0,
            "ch_maxPSI": 100,
            "ch_minPSI": 0,
            "ch_minADC": 4000,
            "ch_maxADC": 32760,
            "ch_enabled": "Enabled"
        }
    }
}
```

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
