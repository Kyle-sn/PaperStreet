#!/bin/sh

DATEVAR="date +%Y%m%d"

/usr/bin/python3 $HOME/PaperStreet/python/research/get_economic_releases.py /tmp/cron_logs/get_economic_releases_$($DATEVAR)_economic_releases.log 2>&1
