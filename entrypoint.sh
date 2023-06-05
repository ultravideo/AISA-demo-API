#!/bin/bash

flask --app src db upgrade

if [[ "$DISABLE_READ_AND_FEED" == "1" ]]; then
    rq worker & flask --app src run -h 0.0.0.0 -p 7655
else
    python read_and_feed.py "$CAMERA_NAME" "$STREAM" & rq worker & flask --app src run -h 0.0.0.0 -p 7655
fi


