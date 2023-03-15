import datetime
from pathlib import Path

import numpy as np

from flask import request, Response
from redis import Redis
import rq
from src import app, roi_storage, video_storage
from tempfile import mkstemp
from flask import jsonify
from werkzeug.http import HTTP_STATUS_CODES


def error_response(code, message=None):
    error = {
        "error": HTTP_STATUS_CODES.get(code, "Unknown error")
    }
    if message:
        error["message"] = message
    response = jsonify(error)
    response.status_code = code
    return response


@app.route("/roi", methods=["POST"])
def post_roi_region():
    data = request.get_json()
    roi_id = data.get("id")
    if roi_id is None:
        roi_id = Path(mkstemp(dir=roi_storage)[1])
    else:
        roi_id = roi_storage / roi_id
        if roi_id.exists():
            return error_response(400, f"roi with the {id=} already exists")

    height = data.get("height")
    width = data.get("width")
    dim = (height, width)
    roi_data = data["data"]
    a = np.ndarray(dim, buffer=np.array(roi_data, dtype=np.int8), dtype=np.int8)

    a.dump(roi_id)

    roi_id = str(roi_id.parts[-1])
    return {
        "id": roi_id,
        "width": width,
        "height": height
    }


@app.route("/roi/<id_>", methods=["PUT"])
def update_roi_region(id_):
    f = roi_storage / id_
    if not f.exists():
        return error_response(400, "roi file does not exist")

    data = request.get_json()

    height = data.get("height")
    width = data.get("width")

    roi_data = np.load(f)
    if roi_data.shape != (height, width):
        return error_response(400, "new roi has different resolution to the old one")

    roi_data[:] = data["data"]
    roi_data.dump(f)

    return {
        "id": id_,
        "width": width,
        "height": height
    }


@app.route("/roi/<id_>", methods=["GET"])
def get_roi_region(id_):
    f = roi_storage / id_
    if not f.exists():
        return error_response(400, "roi file does not exist")

    data = np.load(f)

    return jsonify(
        {
            "id": id_,
            "width": data.shape[1],
            "height": data.shape[0],
        }
    )


@app.route("/roi/<id_>", methods=["DELETE"])
def delete_roi_region(id_):
    f = roi_storage / id_
    if not f.exists():
        return error_response(400, "roi file does not exist")

    f.unlink()
    return {
        "id": id_
    }


@app.route("/encode", methods=["POST"])
def start_encoding():
    data = request.get_json()
    roi_id = data.get("roi_id")
    f = roi_storage / roi_id
    if not f.exists():
        f = None
    try:
        start_point = datetime.datetime.fromisoformat(data.get("start"))
    except (TypeError, ValueError) as e:
        return error_response(400, "Invalid start point" + str(e))
    if datetime.datetime.utcnow() - start_point > datetime.timedelta(minutes=8):
        return error_response(400, "Starting point is too far back in the past, maximum amount is 8 minutes")
    try:
        duration = float(data.get("duration"))
    except TypeError:
        return error_response(400, "duration")
    camera = data.get("camera") or "output"
    a = app.task_queue.enqueue(
        "src.encoder.encode",
        f, start_point, duration, mkstemp()[1], camera
    )
    print(a.get_id())
    return {"id": a.get_id()}


@app.route("/encode/<id_>", methods=["GET"])
def get_encoding(id_):
    f = (Path("videos") / id_).with_suffix(".hevc")
    if f.exists():
        return {
            "id": id_,
            "progress": 100,
            "video_url": f"/video/{id_}.mp4"
        }
    try:
        a = rq.job.Job.fetch(id_, connection=app.redis)
    except rq.exceptions.NoSuchJobError:
        return error_response(404, "no such encode")

    progress = a.meta.get("progress", 0)
    output = {
        "id": id_,
        "progress": progress,
    }
    return output


@app.route("/video/<id_>")
def get_video(id_):
    f = (Path("videos") / id_)
    if not f.exists():
        return error_response(404, "video doesnt exist")
    return Response(f.read_bytes(), mimetype="video/MP4")
