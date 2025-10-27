# Loki

Log monitoring

### Server

Docker image: grafana/loki

### Clients

```shell
sudo apt install promtail
```

Update /etc/promtail/config.yml and /etc/systemd/system/[promtail.service](promtail.service)

Ansible uses [config.yml.j2](config.yml.j2) for config.yml

```shell
sudo systemctl daemon-reload
sudo systemctl restart promtail.service
sudo systemctl status promtail.service
```
