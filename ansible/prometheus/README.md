# Prometheus

Metrics collection

### Server

Docker image: prom/prometheus

Edit the targets section in /etc/prometheus/[prometheus.yml](prometheus.yml) as needed.

This file is not currently deployed by Ansible.

```shell
docker cp prometheus.yml prometheus-1:/etc/prometheus/prometheus.yml

docker restart prometheus-1
```

### Clients

```shell
sudo apt install prometheus-node-exporter

systemctl status prometheus-node-exporter
```
