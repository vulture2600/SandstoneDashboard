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
    for DIR in /sys/bus/w1/devices/28-*; do
        
        TEMP_FILE="$DIR/temperature"
        if [ ! -f "$TEMP_FILE" ]; then
            echo "$DIR: ERROR (temperature file missing)"
            continue
        fi
        
        printf "$DIR: "
        awk '{printf "%.1f°F (Raw: %s)\n", ($1 / 1000.0) * 1.8 + 32, $1}' "$TEMP_FILE"
    done
}
