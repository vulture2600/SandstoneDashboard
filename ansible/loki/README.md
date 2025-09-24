# Loki

Log monitoring

#### Server

Create a container from the grafana/loki Docker image.

#### Clients

```shell
sudo apt install promtail
```

Update /etc/promtail/config.yml and /etc/systemd/system/promtail.service.

See [config.yml.j2](config.yml.j2) and [promtail.service](promtail.service) for examples.

```shell
sudo systemctl daemon-reload
sudo systemctl restart promtail.service
sudo systemctl status promtail.service
```
