# InfluxDB

#### Systemctl for InfluxDB

```shell
sudo systemctl enable influxdb
sudo systemctl disable influxdb

sudo systemctl start influxdb
sudo systemctl stop influxdb
sudo systemctl status influxdb
```

#### Connect to InfluxDB

```shell
# Connect to InfluxDB running on the localhost without the password set:
influx

# Connect to InfluxDb running on another host:
influx -host 192.168.1.10 -username fakeuser -password fakepassword

# Same as above and specify the port and database:
influx -host 192.168.1.10 -port 8086 -username fakeuser -password fakepassword -database SandstoneSensorData
```

#### Databases, Measurements

```sql
-- Show databases (power_monitor_sandstone, SandstoneSensorData):
SHOW databases

-- Use the SandstoneSensorData database:
USE SandstoneSensorData

-- Show measurements (pressures, temps, weather):
SHOW MEASUREMENTS
```

### Tags

```sql
SHOW TAG VALUES FROM temps WITH KEY = title
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

```sql
SHOW TAG VALUES FROM temps WITH KEY = location
```

```
name: temps
key      value
---      -----
location UpSchlRmOutsideTemp
location bootWallOutsideTemp
location bootyWallEnclTemp
location bootyWallWaterTemp
location derrickOutsideTemp
location derrickWallEnclTemp
location derrickWallWaterTemp
location mainFlowEnclTemp
location mainFlowOutsideTemp
location mainFlowWaterTemp
location manifoldTemp
location northEndEnclTemp
location northEndOutsideTemp
location northEndWaterTemp
location schoolRmEnclTemp
location schoolRmOutsideTemp
location schoolRmWaterTemp
location shedInside
location shedOutside
location shedSHT30
location stageWallBoxTemp
location stageWallEnclTemp
location stageWallOutsideTemp
location stageWallWaterTemp
location upSchlRmEnclTemp
location upSchlRmWaterTemp
```

### Queries

```sql
-- List the latest 30 temps taken:
SELECT * FROM temps ORDER BY time DESC LIMIT 30

-- List the latest 30 readings from the Derrick Wall:
SELECT * AS readable_time FROM temps WHERE location = 'derrickWallEnclTemp' ORDER BY time DESC LIMIT 30

-- List the first temp from each day for the last 30 days:
SELECT FIRST("temp") AS first_temp_of_day FROM "temps" WHERE time >= now() - 30d GROUP BY time(1d)

-- Show counts from countable columns:
SELECT count(*) FROM temps

-- List series limit to 5 rows:
SHOW SERIES LIMIT 5
```


### Backup/restore InfluxDB

InfluxDB 1.x

Source

```shell
# Check for the USB drive.
# Something like /dev/sda1 with filesystem type vfat.
lsblk -f

# Mount the filesystem
udisksctl mount -b /dev/sda1

# Run the backup (use path output by udisksctl)
influxd backup -portable /path/to/backup

# Unmount it
udisksctl unmount -b /dev/sda1
```

Destination

```shell
# Move the usb drive to the new host. Check for and mount it as above.

# Run the restore (use path output by udisksctl)
influxd restore -portable /path/to/backup

# Unmount it
udisksctl unmount -b /dev/sda1
```
