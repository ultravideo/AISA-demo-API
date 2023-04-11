import datetime
from pathlib import Path

import numpy as np

from flask import request, Response
from redis import Redis
import rq
from src import app, roi_storage, video_storage, models
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

    roi_data = np.load(f, allow_pickle=True)
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

    data = np.load(f, allow_pickle=True)

    return jsonify(
        {
            "id": id_,
            "width": data.shape[1],
            "height": data.shape[0],
            "data": [int(x) for x in data.flatten()]
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
    f = None
    if roi_id is not None:
        f = roi_storage / roi_id
        if not f.exists():
            return error_response("400", "roi file does not exist")
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
    out_path = data.get("saved_path")
    if out_path is not None:
        out_path = (video_storage / out_path).resolve()
        if out_path.exists():
            return error_response(400, "saved_path already exists")
        if not out_path.is_relative_to(video_storage):
            return error_response(403, "Trying to save to prohibited location")
        t = out_path.parent
        try:
            t.mkdir(exist_ok=True, parents=True)
        except Exception as e:
            return error_response(400, f"Failed to create parent directories: {e}")
        if out_path.suffix.lower() != ".mp4":
            return error_response(400, "saved_path must use .mp4 suffix")

    camera = data.get("camera") or "output"
    a = app.task_queue.enqueue(
        "src.encoder.encode",
        f, start_point, duration, mkstemp()[1], camera, out_path
    )
    print(a.get_id())
    return {"id": a.get_id()}


@app.route("/encode/<id_>", methods=["GET"])
def get_encoding(id_):
    a = models.Encoding.query.filter_by(id=id_).first()
    if a is not None:
        p = Path(a.out_path)
        out = "/". join(p.parts[len(video_storage.parts):])

        # We assume that there is no need for the prefix if the video is stored in an unrelated location
        this_ = (Path(__file__) / ".." / "..").resolve()
        if video_storage.is_relative_to(this_):
            prefix = "/".join(video_storage.parts[len(this_.parts):]) + "/"
        else:
            prefix = ""
        return {
            "id": id_,
            "progress": 100,
            "video_url": f"/{prefix}{out}"
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


@app.route("/<path:path>")
def get_video(path):
    this_ = (Path(__file__) / ".." / "..").resolve()
    if video_storage.is_relative_to(this_):
        prefix = video_storage.parts[len(this_.parts):]
    else:
        prefix = []
    rest = path.split("/")
    for i, (a, b) in enumerate(zip(prefix, rest)):
        if a != b:
            rest = rest[i:]
            break
    if all([a == b for a,b in zip(prefix, rest)]):
        rest = rest[len(prefix):]
    f = (video_storage / "/".join(rest))
    if not f.exists():
        return error_response(404, "video doesnt exist")
    a = models.Encoding.query.filter_by(out_path=str(f)).first()
    if a is None:
        return error_response(404, "video doesnt exist")
    return Response(f.read_bytes(), mimetype="video/MP4")
