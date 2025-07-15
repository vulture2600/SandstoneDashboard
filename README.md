# SandstoneDashboard
Revamping the whole damn thing

#### New plan
1) Each pi write raw 1-wire temp data and ADS1115 raw data to data base #1
2) A central service that pulls data from database #1, compares it to a global config file, sorts/formats it, then write relevant data to database #2
3) Grafana pulls data from database #2 and displays on dashboard

* 1-wire temp sensors are hot swappable, meaning if one goes offline, it will show offline on the dashboard.
* A utility shows all online sensors and current temp, and can be reconfigured in global config file on the fly, and will pick up right where it left off after new sensor is assigned to any place on dashboard.
* Same with pressure sensors

#### Proposal
* Two services on each pi node
* Service 1: collects all 1-wire device folder names and collects each of their current temps, writes to database #1 as "heres everything I have".
* Service 2: search and collect all i2c ADS1115 breakout boards and queries all of their input values and writes them to database #1 as raw data, "heres everything i have".

#### Config file
* 1-wire temp sensor data:
    * roomID -> "room name/sensorID"
    * pressure sensors: pi -> i2c addresses -> channels
