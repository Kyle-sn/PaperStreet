#!/bin/sh

DATEVAR=$(date +%Y%m%d)
SYMBOLS="SP500 NASDAQCOM VIXCLS DGS10"

for SYMBOL in $SYMBOLS; do
    /usr/bin/python3 $HOME/PaperStreet/python/research/get_fred_data.py --symbol "$SYMBOL" > /tmp/cron_logs/${DATEVAR}_get_fred_data_${SYMBOL}.log 2>&1
done
