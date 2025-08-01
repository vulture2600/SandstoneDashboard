# Systemd services

Service files should be in **/etc/systemd/system/**

#### systemctl

```shell
# Enable, start and get status for the getSHT30 service:
sudo systemctl enabled getSHT30.service
sudo systemctl start getSHT30.service

sudo systemctl status getSHT30.service
```

```shell
# Run when service files (unit definitions) are updated:
sudo systemctl daemon-reload

# Run when the respective Python script is updated:
sudo systemctl restart getPressures.service
sudo systemctl restart getSHT30.service
sudo systemctl restart getTemps.service
sudo systemctl restart getWeather.service
```

#### journalctl

```shell
# Follow the Systemd journal, only show getTemps.service unit lines:
journalctl -u getTemps.service -f
```

#### Combined example
```shell
sudo systemctl restart getTemps.service && journalctl -u getTemps.service -f
```
