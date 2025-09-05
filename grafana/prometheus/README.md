# Prometheus

Metrics collection

#### Clients

```shell
sudo apt install prometheus-node-exporter

systemctl status prometheus-node-exporter
```

#### Server

Create a container from the prom/prometheus Docker image.

Replace RASPBERRYPPI_IP_ADDR with the IP address of the Raspberry Pi in /etc/prometheus/[prometheus.yml](prometheus.yml)
