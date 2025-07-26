# SandstoneDashboard
Revamping the whole damn thing.


New plan:
1)have each pi write raw 1-wire temp data and ADS1115 raw data to data base #1
2) have a central service that pulls data from database #1, compares it to a global config file, sorts/formats it, then write relevant data to database #2
3) grafana pulls data from database #2 and displays on dashboard


1-wire temp sensors are hot swappable, meaning if one goes offline, it will show offline on the dashboard.
A utility shows all online sensors and current temp, and can be reconfigured in global config file on the fly, and will pick up right where it left off after new sensor is assigned to any place on dashboard.
same with pressure sensors.

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

#### To do

##### Python script updates:

* Create the master config json file

* Update the Python scripts to pull the sensor config file each time with the most recent local copy as the fallback

* The config file will be hosted on a Windows share on the NAS

* The assign_sensors script will need to be run which will update the sensor config file on the NAS Windows share

* The sensor config file should be committed to a separate branch on the GitHub repo

* For data integrity, the records should contain the sensor_id with the location

* The .env files should have the path to the the master sensor config file


## Sandstone Data Pipeline

#### Data Source

* 1-Wire temperature sensors
* i2c pressure sensors
* i2c humidity sensors

#### Data Ingestion

* SystemD driven Python scripts used to read sensor data

#### Storage

* Data is written to InfluxDB

#### Visualization, Monitoring, Alerting

* Grafana for the dashboard
* Slack or Discord alert channels
