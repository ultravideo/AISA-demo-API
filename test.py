import datetime
import json
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
preprocess_roi(temp["id"])

l = datetime.datetime.now()

a = requests.request(
    "POST",
    "http://127.0.0.1:5000/encode",
    json={
        "roi_id": temp["id"],
        "start": (datetime.datetime.utcnow() - datetime.timedelta(seconds=60)).isoformat(),
        "duration": 12,
    }
)
print(a.text)
