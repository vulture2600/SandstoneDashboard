# Systemd services

Copy the service files to **/etc/systemd/system/** and follow this example to enable and start the services.

#### systemctl

```shell
sudo systemctl enabled getSHT30.service
sudo systemctl start getSHT30.service

sudo systemctl status getSHT30.service
```

```shell
# Use when service files (unit definitions) are updated:
sudo systemctl daemon-reload

# Use when the Python script, run by the service, is updated:
sudo systemctl restart getSHT30.service
```

#### journalctl

```shell
# Follow the Systemd journal, only show getTemps.service unit lines:
journalctl -u getTemps.service -f
```
