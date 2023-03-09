import json
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
