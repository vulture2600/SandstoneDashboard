#!/usr/bin/bash
# Backup SandstoneDashboard sensor config files to S3 bucket 
# Verify /etc/hosts has an entry for quobjects

set -euo pipefail  # Exit on error, unset variable, or error in pipeline

S3_URL="http://quobjects"
BUCKET="s3://sandstonedashboard-config"
SOURCE_DIR="/home/pi/SandstoneDashboard/config"
VIRT_ENV_DIR=/home/pi/sensor_config_s3_sync
AWS="$VIRT_ENV_DIR/venv_s3/bin/aws"

"$AWS" s3 sync "$SOURCE_DIR" "$BUCKET" \
    --endpoint-url "$S3_URL" \
    --exclude "*" \
    --include "*.json" \
    --exclude "*bak*"
