# oneWireTemps

Code adapted from weatherStation along with OneWire sensors is being used to monitor ice farming at the [Sandstone Ice Park](https://www.mountainproject.com/area/106915985/sandstone-ice-park).

### Systemd

Python files in [src](src) are driven by [Systemd services](systemd)

### InfluxDB

[InfluxDB](influxdb.md) - The time series database used to store the OneWire sensor data.

### Alerting

[Alerting](alerting.md) - Eventually through the alerts feature in Grafana and either Slack or Discord.

### Issues

[Issues](issues.md)

### Change log

[Change log](change_log.md)
