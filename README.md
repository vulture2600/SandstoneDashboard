# SandstoneDashboard

This is for the monitoring the ice making at the [Sandstone Ice Park](https://www.mountainproject.com/area/106915985/sandstone-ice-park) in Sandstone MN.

## Sensor config file

We are implementing a master sensor config file for 1-Wire and i2c sensor connected Raspberry Pi's.

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

* See [Issues](issues.md) for more.


## Sandstone Data Pipeline

#### Data Source

* 1-Wire temperature sensors
* i2c pressure sensors
* i2c humidity sensors

#### Data Ingestion

* [SystemD](systemd) driven Python [scripts](src) used to read sensor data

#### Storage

* OneWire sensor data is written to [InfluxDB](influxdb.md) - time series database

#### Visualization, Monitoring, Alerting

* Grafana for the dashboard
* Slack or Discord alert channels
* See [Alerting](alerting.md) for more
