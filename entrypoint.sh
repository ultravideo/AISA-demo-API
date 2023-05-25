#!/bin/bash

flask --app src db upgrade
python read_and_feed.py & rq worker & flask --app src run -h 0.0.0.0 -p 7655

