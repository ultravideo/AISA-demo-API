import datetime
import json
from pathlib import Path

import requests
from src.encoder import preprocess_roi

width = (1920 + 63) // 64
height = (1080 + 63) // 64

a = requests.request(
    "POST",
    "http://127.0.0.1:5000/roi",
    json={
        "width": width,
        "height": height,
        "data": [x % 2 for x in range(width * height)]
    },

)

temp = json.loads(a.text)
print(temp)


a = requests.request(
    "GET",
    f"http://127.0.0.1:5000/roi/{temp['id']}"
)
print(json.loads(a.text))
preprocess_roi(temp["id"])

l = datetime.datetime.now()

a = requests.request(
    "POST",
    "http://127.0.0.1:5000/encode",
    json={
        "roi_id": temp["id"],
        "start": (datetime.datetime.utcnow() - datetime.timedelta(seconds=60)).isoformat(),
        "duration": 12,
        "saved_path": str((Path(__file__) / ".." / "video_name.mp4").resolve())
    }
)
print(a.text)
