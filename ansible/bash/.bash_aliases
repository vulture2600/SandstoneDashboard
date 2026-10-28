## Common Shell Commands

if command -v lsd >/dev/null; then
    alias als='alias ls=lsd'
    alias lt='lsd --tree'
    alias ltd='lsd --tree -d'
    alias lt1='lsd --tree --depth 1'
    alias lt2='lsd --tree --depth 2'
    alias lt3='lsd --tree --depth 3'
fi

alias ll='ls -l'
alias la='ls -A'
alias lla='ls -lA'
alias lrt='ls -lrt'
alias lart='ls -lArt'
alias lrS='ls -lrS'
alias larS='ls -lArS'

command -v batcat >/dev/null && alias bat=$(which batcat)

## Networking

alias inet='{ ip addr || ifconfig; } 2> /dev/null | grep -w inet'

alias nntp='netstat -ntp | grep -v ^tcp6'
alias nntpa='netstat -antp | grep -v ^tcp6'

## Misc

alias tpls='tps1; als'
alias activate='source .venv/bin/activate'

## Object Storage

alias avs3='source ~/sensor_config_s3_sync/venv_s3/bin/activate'
alias s3lv='aws s3api list-object-versions --bucket sandstonedashboard-config'

## 1-Wire temperature sensers

alias check1w='for FILE in /sys/bus/w1/devices/28-*; do printf "$FILE "; cat "$FILE/temperature"; done'

alias check1wl='while true; do date "+%F %T"; check1w; sleep 2; echo; done'

alias checktemp='for FILE in /sys/bus/w1/devices/28-*/temperature; do printf "$FILE: "; awk '\''{printf "%.1f°F\n", ($1 / 1000.0) * 1.8 + 32}'\'' "$FILE"; done'

alias checktempl='while true; date "+%F %T"; do checktemp; sleep 2; echo; done'
