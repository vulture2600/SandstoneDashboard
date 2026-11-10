## Toggle prompt set by $PS1 (pseudo terminal prompt 1) between short and long.

PS1_PREFIX="\[\e]0;\u@\h: \w\a\]\[\033[01;32m\]\u@"
PS1_SUFFIX="\[\033[00m\]:\[\033[01;34m\]\w $\[\033[00m\] "
HOSTNAME_DEFAULT="\h"

declare -A hostname_map
hostname_map["$HOSTNAME"]="$HOSTNAME_DEFAULT"
hostname_map["$HOSTNAME_DEFAULT"]="$HOSTNAME"

hostname_map["SandstoneRasPi4b8GbPowerMonitor"]="shed"
hostname_map["shed"]="SandstoneRasPi4b8GbPowerMonitor"

hostname_map["SandstonePi3bPlusSchoolRoom"]="schoolroom"
hostname_map["schoolroom"]="SandstonePi3bPlusSchoolRoom"

hostname_map["SandstoneRasPi3BPlusStageWall"]="stagewall"
hostname_map["stagewall"]="SandstoneRasPi3BPlusStageWall"

HOSTNAME_CURRENT=$HOSTNAME

tps1() {
    if [[ -n "$VIRTUAL_ENV" ]]; then
        echo "Not while the virtualenv is active"
        return
    fi

    HOSTNAME_CURRENT=${hostname_map[$HOSTNAME_CURRENT]}
    PS1="${PS1_PREFIX}${HOSTNAME_CURRENT}${PS1_SUFFIX}"
}


## Update system packages

APT_UPD_CMD="sudo apt update; echo
sudo apt -y dist-upgrade; echo
sudo apt -y autoremove; echo"

upd() {
    MONTH=$(date "+%m")

    if [ $MONTH -eq 12 ]; then
        echo "Code freeze, no system updates in December"
        return
    fi

    echo -e "$APT_UPD_CMD\n"
    eval "$APT_UPD_CMD"
    date >> ~/.upd.log
}


## Update Python packages. Activate the virtual environment before using.

REQUIREMENTS_FILE="/tmp/requirements-upp.txt"

upp() {
    pip install --upgrade pip setuptools || return
    OUTDATED=$(pip list --outdated) || return
    test -z "$OUTDATED" && return
    echo "$OUTDATED"

    pip freeze > $REQUIREMENTS_FILE || return
    sed -i 's/==/>=/g' $REQUIREMENTS_FILE || return
    pip install -r $REQUIREMENTS_FILE --upgrade | grep -v 'Requirement already satisfied'
    rm $REQUIREMENTS_FILE
    echo
    pip list --outdated
}


## Check all Sandstone Dashboard services

declare -A service_map
service_map["SandstoneRasPi4b8GbPowerMonitor"]="getTemps.service getPressures.service getSHT30.service
                                                getWeather.service sensor_config_backup.timer promtail.service
                                                prometheus-node-exporter.service"
service_map["SandstoneRasPi3BPlusStageWall"]="getTemps.service promtail.service prometheus-node-exporter.service"
service_map["SandstonePi3bPlusSchoolRoom"]="getTemps.service promtail.service prometheus-node-exporter.service"

checkservices() {
    for SERVICE in ${service_map[$HOSTNAME]}; do
        printf '%-35s %s\n' "$SERVICE" "$(systemctl is-active "$SERVICE")"
    done
}


## Check 1-Wire temperature sensors

checktemps() {
    if [[ "$1" == "-h" || "$1" == "--help" ]]; then
        echo "Check 1-Wire temperature sensors and display their readings in Fahrenheit with color coding."
        echo "Usage: checktemps [-l] [-n]"
        echo "  -l: Loop every 5 seconds"
        echo "  -n: Suppress title lookup from config file"
        return
    fi

    local dir temp_file device_id title

    while true; do
        date "+%F %T"

        for dir in /sys/bus/w1/devices/28-*; do
            temp_file="$dir/temperature"

            if [[ ! -f "$temp_file" ]]; then
                echo "$dir: ERROR (temperature file missing)"
                continue
            fi

            title=""
            device_id=$(basename "$dir")
            if [[ ! " $* " =~ " -n " ]]; then
                title=$(viewconfig "$device_id" -t 2>/dev/null)
            fi

            printf "%s: " "$temp_file"

            awk -v title="$title" '{
                temp = ($1 / 1000.0) * 1.8 + 32  # Bad or missing data is treated as 0 and converted to 32°F

                if (temp <= 32)
                    color = "\033[38;5;75m"  # Cornflower blue
                else if (temp < 34)
                    color = "\033[96m"  # Cyan
                else if (temp < 50)
                    color = "\033[32m"  # Green
                else
                    color = "\033[93m"  # Yellow

                printf "%6s %s%5.1f°F\033[0m %s\n", $1, color, temp, title
            }' "$temp_file"
        done

        [[ ! " $* " =~ " -l " ]] && break
        sleep 5
    done
}


# View configuration for 1-Wire temperature sensors

viewconfig() {
    if [[ "$1" == "-h" || "$1" == "--help" ]]; then
        echo "View configuration for 1-Wire temperature sensors from the Sandstone Dashboard config file."
        echo "Usage: viewconfig <device_id match> [-t]"
        echo "  -t: Show only the title of the sensor"
        return
    fi

    local config="$HOME/SandstoneDashboard/config/getTemps.json"

    if [[ ! -f "$config" ]]; then
        echo "Config file not found: $config" >&2
        return 1
    fi

    if [[ -z "$1" ]]; then
        jq --arg host "$HOSTNAME" '.[$host]' "$config"
        return
    fi

    local pattern="$1"

    if [[ "$2" == "-t" ]]; then
        jq --arg host "$HOSTNAME" --arg pattern "$pattern" \
           -r '.[$host] | .[] | select(.id | contains($pattern)) | .title' \
           "$config"
    else
        jq --arg host "$HOSTNAME" --arg pattern "$pattern" \
           -r '.[$host] | with_entries(select(.value.id | contains($pattern)))' \
           "$config"
    fi
}

## Test InfluxDB connection

checkinflux() {
    if [[ "$1" == "-h" || "$1" == "--help" ]]; then
        echo "Test InfluxDB connection using the .env file in SandstoneDashboard."
        echo "Usage: checkinflux [-v]"
        echo "  -v: Verbose output"
        return
    fi
    
    local env_file="$HOME/SandstoneDashboard/.env"
    local curl_opts=(-fsS)
    local magenta="\033[95m"
    local reset="\033[0m"


    if [[ "$1" == "-v" ]]; then
        curl_opts=(-fv)
    fi

    source "$env_file" || return 1

    if curl "${curl_opts[@]}" "http://$INFLUXDB_HOST:$INFLUXDB_PORT/ping"; then
        printf "Connection to $INFLUXDB_HOST:$INFLUXDB_PORT ${magenta}succeeded${reset}\n"
    else
        printf "Connection to $INFLUXDB_HOST:$INFLUXDB_PORT failed\n"
        return 1
    fi
}


## Sandstone Dashboard commands and logs

ssdcommands() {
    local -a BAT_CMD=(cat)

    if command -v batcat >/dev/null 2>&1; then
        BAT_CMD=(batcat -pp -l bash)
    elif command -v bat >/dev/null 2>&1; then
        BAT_CMD=(bat -pp -l bash)
    fi

    test -f ~/.ascii_nomic.txt && { echo; cat ~/.ascii_nomic.txt; }
    "${BAT_CMD[@]}" /etc/motd

    "${BAT_CMD[@]}" <<'EOF'
  --- Application Logs ---
tail -f /var/log/SandstoneDashboard/getTemps.log      # Follow getTemps.log
tail -f /var/log/SandstoneDashboard/getPressures.log  # Follow getPressures.log
tail -f /var/log/SandstoneDashboard/getSHT30.log      # Follow getSHT30.log
tail -f /var/log/SandstoneDashboard/getWeather.log    # Follow getWeather.log
tail -f /var/log/SandstoneDashboard/get*.log          # Follow all logs
lnav /var/log/SandstoneDashboard/get*.log             # Follow all logs w/ lnav

  --- Service Logs (Journal) ---
journalctl -fu getTemps.service               # Follow journal for getTemps
journalctl -fu getPressures.service           # Follow journal for getPressures
journalctl -fu getSHT30.service               # Follow journal for getSHT30
journalctl -fu getWeather.service             # Follow journal for getWeather

  --- Systemd Services ---
systemctl status getTemps.service             # Status of getTemps.service
systemctl status getPressures.service         # Status of getPressures.service
systemctl status getSHT30.service             # Status of getSHT30.service
systemctl status getWeather.service           # Status of getWeather.service

  --- System Monitoring ---
systemctl --failed                      # List any failed services
df -hT                                  # Show disk usage
free -h                                 # Show memory usage
uptime                                  # Show system uptime, load averages
top                                     # Show processes, also try htop or btop
ps -fu pi                               # Show processes for the pi user
cat /proc/device-tree/model; echo       # Show Raspberry Pi model
uname -r                                # Show Linux kernel version

EOF
}
