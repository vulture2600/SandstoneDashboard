# Prometheus

Metrics collection

#### Server

Docker image prom/prometheus

Replace RASPBERRYPPI_IP_ADDR with the IP address of the Raspberry Pi in /etc/prometheus/[prometheus.yml](prometheus.yml)

This file is not configured by Ansible.

#### Clients

```shell
sudo apt install prometheus-node-exporter

systemctl status prometheus-node-exporter
```
