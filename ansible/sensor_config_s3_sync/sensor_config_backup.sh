#!/usr/bin/bash
# Backup SandstoneDashboard sensor config files to s3 bucket 
# Check /etc/hosts for quobjects

VIRT_ENV_DIR=/home/pi/sensor_config_s3_sync

cd $VIRT_ENV_DIR || exit 1
source venv_s3/bin/activate || exit 1

aws s3 sync /home/pi/SandstoneDashboard/config \
    s3://sandstonedashboard-config \
    --endpoint-url http://quobjects \
    --exclude "*" \
    --include "*.json" \
    --exclude "*bak*"

echo "Backup complete"
