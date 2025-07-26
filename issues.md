# Issues

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
