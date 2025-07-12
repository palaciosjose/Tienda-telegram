#!/bin/bash
while true; do
    if ! pgrep -f "python3.*bot_working.py" > /dev/null; then
        echo "Bot detenido - Reiniciando... $(date)" >> bot_restart.log
        cd /home/serverbussn/prueba.sdpro.shop
        python3 bot_working.py >> bot_working.log 2>&1 &
    fi
    sleep 30
done
