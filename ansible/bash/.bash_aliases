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

alias checktempsl='while true; date "+%F %T"; do checktemps; sleep 2; echo; done'
