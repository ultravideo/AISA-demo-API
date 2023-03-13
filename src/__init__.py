import rq
from flask import Flask
import pathlib
from redis.client import Redis

roi_storage = pathlib.Path("rois").absolute()
if not roi_storage.exists():
    roi_storage.mkdir()
video_storage = pathlib.Path("videos").absolute()
if not video_storage.exists():
    video_storage.mkdir()

app = Flask(__name__)
app.redis = Redis.from_url("redis://")
app.task_queue = rq.Queue(connection=app.redis)

from . import api
from .encoder import ffmpeg_concat_and_pipe_partial_videos, encode
