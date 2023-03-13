import datetime
import json
import requests
from src import ffmpeg_concat_and_pipe_partial_videos

a = requests.request(
    "POST",
    "http://127.0.0.1:5000/roi",
    json={
        "type": "txt",
        "roi": "2 2 12 0 12 0"
    },

)

temp = json.loads(a.text)

a = requests.request(
    "POST",
    "http://127.0.0.1:5000/encode",
    json={
        "roi_id": temp["id"],
        "start": (datetime.datetime.now() - datetime.timedelta(seconds=60)).isoformat(),
        "duration": 12,
    }
)
print(a.text)
