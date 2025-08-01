# SandstoneDashboard

![Grafana Dashboard](readme_images/grafana_dashboard.jpg)

The SandstoneDashboard monitors the ice making at the [Sandstone Ice Park](https://www.mountainproject.com/area/106915985/sandstone-ice-park) in Sandstone MN. The main focus is monitoring the water lines that carry water to edge of the cliffs and preventing them from freezing entirely. Significant manual intervention is required when lines freeze or break.

See [Current Efforts](docs/current_efforts.md) for more.

## Data Pipeline

#### Data Source

* Adafruit ADS1115 Analog-to-Digital converter used to measure water pressure
* Adafruit SHT30 Humidity and Temperature Sensor
* Adafruit 1-Wire temperature sensor
* [Open Weather API](https://openweathermap.org/api)

#### Data Ingestion

[SystemD](ansible/systemd) driven Python [scripts](src):
* getPressures.service
* getSHT30.service
* getTemps.service
* getWeather.service

#### Data Storage

* I2C and 1-Wire sensor data is written to [InfluxDB](docs/influxdb.md) time series database

#### Visualization, Monitoring, and Alerting

* Grafana dashboard
* Slack or Discord alert channels
* See [Alerting](docs/alerting.md) for more
