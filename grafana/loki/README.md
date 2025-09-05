# Loki

Log aggregation

#### Clients

```shell
sudo apt install promtail

sudo systemctl status promtail.service
```

Replace LOKI_IP_ADDR with the ip address of Loki container in /etc/promtail/[config.yml](config.yml)

#### Server

Create a container from the grafana/loki Docker image.
