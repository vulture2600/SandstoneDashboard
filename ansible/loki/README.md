# Loki

Log monitoring

### Server

Docker image: grafana/loki

[local-config.yaml](local-config.yaml) is not currently deployed by Ansible.

```shell
docker cp local-config.yaml loki-3:/etc/loki/local-config.yaml

docker restart loki-3
```

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
