# Backup sensor config files to S3

This sets up automatic backups of SandstoneDashboard sensor config files
to S3 storage created in QNAP QuObjects.

1) Copy the AWS [config](config) file to ~/.aws/

1) Add the access key and secret key to ~/.aws/credentials

1) Append the following line to /etc/hosts. Update the IP address if different.

    ```192.168.30.10   quobjects```

1) Create and cd to the script directory

    ```shell
    mkdir ~/sensor_config_s3_sync
    cd ~/sensor_config_s3_sync
    ```

1) Copy in [sensor_config_backup.sh](sensor_config_backup.sh) and [requirements.txt](requirements.txt)

1) Create the virtual environment

    ```shell
    python -m venv venv_s3
    source venv_s3/bin/activate
    pip install -r requirements.txt
    ```

1) Copy [sensor_config_backup.service](sensor_config_backup.service) and [sensor_config_backup.timer](sensor_config_backup.timer) to /etc/systemd/system/

1) Enable and start the sensor_config_backup service

    ```shell
    sudo systemctl daemon-reload
    sudo systemctl enable sensor_config_backup.timer
    sudo systemctl start sensor_config_backup.timer
    ```

### Verification

Check that the timer is active

```shell
systemctl list-timers | grep sensor_config_backup
```

View logs

```shell
journalctl -u sensor_config_backup.service -f
```

### List objects in the bucket

Activate the virtual environment

```shell
source ~/sensor_config_s3_sync/venv_s3/bin/activate
```

List buckets, contents, and versions

```shell
aws s3 ls                            # list buckets
aws s3 ls sandstonedashboard-config  # list bucket contents

aws s3api list-object-versions --bucket sandstonedashboard-config
```
