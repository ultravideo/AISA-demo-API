import json

from src import ffmpeg_concat_and_pipe_partial_videos, encode

import requests

a = requests.request(
    "POST",
    "http://127.0.0.1:5000/roi",
    json={
        "type": "txt",
        "roi": "2 2 12 0 12 0"
    },

)

print(a.text)

temp = json.loads(a.text)

# ffmpeg_concat_and_pipe_partial_videos(17.4, 25)
#encode("rois/5.txt", 12, 5, "out2.hevc")

a = requests.request(
    "POST",
    "http://127.0.0.1:5000/encode",
    json={
        "roi_id": temp["id"],
        "start": 50,
        "duration": 12,
    }
)
print(a.text)