# Current Efforts

## Sensor config file

We are implementing a master sensor config file for 1-Wire and i2c sensors connected Raspberry Pi's.

#### Requirements

* 1-wire temp sensors are hot swappable. If one goes offline, it should show as offline on the dashboard.
* A utility shows all online sensors and current temp, and can be reconfigured in global config file on the fly, and will pick up right where it left off after new sensor is assigned to any place on dashboard.
* Same with pressure sensors.

#### Format

* 1-Wire temp sensors
    * Raspberry Pi hostname
        * Room ID
            * Sensor ID
            * Room name
* i2c pressure sensors
    * Raspberry Pi hostname
        * Room ID
            * i2c addresses
            * Channels
* i2c humidity sensors
    * Raspberry Pi hostname
        * Room ID
            * i2c addresses
            * Channels

##### Python script updates:

* Create the master config json file

* Update the Python scripts to pull the sensor config file each time with the most recent local copy as the fallback

* The config file will be hosted on a Windows share on the NAS

* The assign_sensors script will need to be run which will update the sensor config file on the NAS Windows share

* The sensor config file should be committed to a separate branch on the GitHub repo

* For data integrity, the records should contain the sensor_id with the location

* The .env files should have the path to the the master sensor config file


## Issues

### Data types in InfluxDB affecting alerting

Because temp and humidity columns (key fields) are string types and not floats in the SandstoneSensorData.temps table, alerts in Grafana fail to evaluate. This is because they cannot compare string values to float/int values set as the alerting threshold in Grafana. See the following examples.

```sql
SELECT last(temp) FROM temps WHERE location = 'stageWallOutsideTemp'
```

```
name: temps
time                last
----                ----
1751153102963487979 77.6
```

```sql
SHOW FIELD KEYS FROM "temps"
```

```
name: temps
fieldKey  fieldType
--------  ---------
humidity  string
temp      string
timeStamp string
```

Solution

* The [getTemps.py](src/getTemps.py) script has been updated to convert the temp to a float and skip the room when the temp is not collected. The other Python scripts dealing with temp and humidity should be updated in a similar fasion.

```python
"fields": {
    "temp_flt": float(temp)
}
```

```phython
if temp == "Off":
    print(f"temp is {temp}, skipping room {room_id}")
    continue
```
