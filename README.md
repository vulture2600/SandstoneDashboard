# SandstoneDashboard

![Grafana Dashboard](readme_images/grafana_dashboard.jpg)

The SandstoneDashboard monitors the ice making at the [Sandstone Ice Park](https://www.mountainproject.com/area/106915985/sandstone-ice-park) in Sandstone MN. The main focus is monitoring the water lines that carry water to edge of the cliffs and preventing them from freezing entirely. Significant manual intervention is required when lines freeze or break.

See [Current Efforts](current_efforts.md) for more.

## Data Pipeline

#### Data Source

* Adafruit 1-Wire temperature sensors
* Adafruit SHT30 temp and humidity sensors (i2c)
* [Open Weather API](https://openweathermap.org/api)

#### Data Ingestion

[SystemD](systemd) driven Python [scripts](src):
* getTemps.service
* getSHT30.service
* getWeather.service

#### Data Storage

* OneWire sensor data is written to [InfluxDB](influxdb.md) time series database

#### Visualization, Monitoring, and Alerting

* Grafana dashboard
* Slack or Discord alert channels
* See [Alerting](alerting.md) for more
