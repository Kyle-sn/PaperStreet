#!/bin/sh

DATEVAR=$(date +%Y%m%d)

/usr/bin/python3 $HOME/PaperStreet/python/research/get_economic_releases.py > /tmp/cron_logs/${DATEVAR}_economic_calendar.log 2>&1

