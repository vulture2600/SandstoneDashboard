# Systemd services

Service files should be in /etc/systemd/system/

### systemctl

Enable, start and get status for the getSHT30 service:
```shell
sudo systemctl enabled getSHT30.service
sudo systemctl start getSHT30.service
sudo systemctl status getSHT30.service
```

Run when service files (unit definitions) are updated:
```shell
sudo systemctl daemon-reload
```

Run when the respective Python script is updated:
```shell
sudo systemctl restart getPressures.service
sudo systemctl restart getSHT30.service
sudo systemctl restart getTemps.service
sudo systemctl restart getWeather.service
```

### journalctl

Follow the Systemd journal, only show getTemps.service unit lines:
```shell
journalctl -u getTemps.service -f
```

### Combined example

```shell
sudo systemctl restart getTemps.service && journalctl -u getTemps.service -f
```
