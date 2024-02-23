#!/bin/bash
if [ ! -e /data/.env ]; then
    cp example.env /data/.env
fi
if [ ! -e /data/config.yaml ]; then
    cp config.yaml /data/config.yaml
fi

python -m hordalan_discord.checkin
