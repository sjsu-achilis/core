#!/bin/bash

python $PYTHONPATH/core/simulate_players.py 2>&1 >> /logs/core$(date +%Y_%m_%d).log &

sleep 5

gunicorn --bind 0.0.0.0:80 core.wsgi 2>&1 | tee -a /logs/core$(date +%Y_%m_%d).log
