import rq
from flask import Flask
import pathlib
import os
from redis.client import Redis

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

roi_storage = pathlib.Path("rois").absolute()
if not roi_storage.exists():
    roi_storage.mkdir()
video_storage = pathlib.Path("/").absolute()
if not video_storage.exists():
    video_storage.mkdir()

app = Flask(__name__)
redis_url = os.environ["REDIS_URL"] or "redis://"
app.redis = Redis.from_url(redis_url)
app.config["SQLALCHEMY_DATABASE_URI"] = f'sqlite:///{(pathlib.Path(__file__) / ".." / ".." / "data" / "app.db").resolve()}'
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.task_queue = rq.Queue(connection=app.redis)
db = SQLAlchemy(app)

migrate = Migrate(app, db, render_as_batch=True, compare_type=True)

from . import api
from .encoder import ffmpeg_concat_and_pipe_partial_videos, encode

import src.models
