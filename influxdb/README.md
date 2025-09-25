# InfluxDB

Docker image influxdb:1.8

#### Connect to InfluxDB

```shell
# Connect to InfluxDB running on the localhost:
influx

# Connect to InfluxDb running on another host:
influx -host 192.168.1.10 -username <user> -password <password>

# Same as above and specify the port and database:
influx -host 192.168.1.10 -port 8086 -username <user> -password <password> -database <database>
```

### Comparison with SQL databases


| InfluxDB        | SQL Equivalent                  | Notes                                             |
| --------------- | ------------------------------- | ------------------------------------------------- |
| Measurement | Table                           |
| Tag set     | Indexed columns (labels)        | Defines "dimensions" — like `location="Minneapolis"`  |
| Field set   | Data columns (values)           | Not indexed — stores actual measurements          |
| Point       | Row                             | A single data record (time + tag set + field set) |
| Series      | Group of rows (points) with same tag set | Filtered view of a measurement             |

### Measurements

```sql
use <database>

show measurements
```

```sql
name: measurements
name
----
temps
weather
```

### Series

```sql
show series                      -- show all series for the database
show series from weather         -- show series for the measurement weather
show series from autogen.weather -- same as above, include the retention policy
```

```
key
---
weather,location=Minneapolis
weather,location=Sandstone
```

#### Key fields for the series

```sql
show field keys from weather
```

```
name: weather
fieldKey               fieldType
--------               ---------
currentCondition       string
dailyCondition         string
dailyConditionTomorrow string
feelsLike              float
humidity               integer
tempHigh               float
tempHighTomorrow       integer
tempLow                float
tempLowTomorrow        float
timeStamp              string
windDirection          integer
windGust               float
windSpeed              float
```

#### Point example as json

```json
{
    "measurement": "weather",
    "tags": {
        "location": "Sandstone"
    },
    "fields": {
        "currentCondition": "Clear",
        "dailyCondition": "Clear",
        "dailyConditionTomorrow": "Clear",
        "feelsLike": 53.04,
        "humidity": 100,
        "tempHigh": 76.93,
        "tempHighTomorrow": 75,
        "tempLow": 53.31,
        "tempLowTomorrow": 51.69,
        "timeStamp": "2025-08-01 08: 20: 31",
        "windDirection": 0,
        "windSpeed": 0.0,
        "windGust": 8.86
    }
}
```

Total number of unique series (combination of measurement and tags):

```sql
show series cardinality
```

```
cardinality estimation
----------------------
6
```

#### Tags

```sql
show tag values from temps with key = title
```

```
name: temps
key   value
---   -----
title Booty Wall Enclosure Temp
title Booty Wall Outside Temp
title Booty Wall Water Temp
title Derrick Wall Enclosure Temp
title Derrick Wall Outside Temp
title Derrick Wall Water Temp
title Main Flow Enclosure Temp
title Main Flow Outside Temp
title Main Flow Water Temp
title Manifold Temp
title North End Enclosure Temp
title North End Outside Temp
title North End Water Temp
title School Room Enclosure Temp
title School Room Outside Temp
title School Room Water Temp
title Shed Inside
title Shed Outside
title Shed SHT30
title Stage Wall Box Temp
title Stage Wall Enclosure Temp
title Stage Wall Outside Temp
title Stage Wall Water Temp
title Upper SchlRm Enclosure Temp
title Upper School Room Outside Temp
title Upper School Room Water Temp
```

#### Query examples

```sql
-- List the latest 10 temps taken:
select * from temps order by time desc limit 10

-- List the latest 10 temps from the School Room:
select * from temps where location = 'schoolRmOutsideTemp' order by time desc limit 10

-- Show the last School Room temp:
select last(temp_flt), title from temps where location = 'schoolRmOutsideTemp'

-- List the first temps of each day from the Stage Wall for the last 30 days:
select first(temp_flt) as first_temp_of_day, title from temps where location = 'stageWallOutsideTemp' and time >= now() - 30d group by time(1d)

-- Show counts from countable columns in temps:
select count(*) from temps
```

#### Grafana queries

InfluxQL in Grafana for the latest:

```sql
select last(*) from autogen.weather

select last(*) from weather
```

Grafana uses the time of the most recent point as the default timestamp in Stat or Time series panels.

* last(*): Selects the most recent value of every field in the weather measurement.
* "autogen": Default retention policy
* "weather": Measurement (like an SQL table)

#### Retention policies

```sql
show retention policies

show retention policies on <database>

create retention policy "180_days" on <database> duration 180d replication 1 default
```

## Backup/restore InfluxDB

InfluxDB 1.x, backup using a USB drive

#### Source

```shell
# Check for the USB drive.
# Something like /dev/sda1 with filesystem type vfat.
lsblk -f

# Mount the filesystem
udisksctl mount -b /dev/sda1

# Create a backup dir, example
cd /media/pi/89E1-A8CA/
mkdir influxdb_backup.2025.08.30

# Run the backup (use path output by udisksctl)
influxd backup -portable /path/to/backup

# Unmount it
udisksctl unmount -b /dev/sda1
```

#### Destination

```shell
# Move the usb drive to the new host. Check for and mount it as above.

# Run the restore (use path output by udisksctl)
influxd restore -portable /path/to/backup

# Unmount it
udisksctl unmount -b /dev/sda1
```
