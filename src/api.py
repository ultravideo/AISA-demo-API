import datetime
from pathlib import Path

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
    print(data)
    roi_type = data.get("type")
    if roi_type not in ("txt", "bin"):
        return error_response(400, "invalid type for roi")
    roi_id = data.get("id")
    if roi_id is None:
        roi_id = Path(mkstemp(f".{roi_type}", dir=roi_storage)[1])
    else:
        roi_id = video_storage / roi_id
        if roi_id.exists():
            return error_response(400, f"roi with the {id=} already exists")

    with roi_id.open("w" if roi_type == "txt" else "wb") as f:
        f.write(data["roi"])

    roi_id = str(roi_id.parts[-1])
    return {
        "id": roi_id.split(".")[0],
        "type": roi_id.split(".")[1],
    }


@app.route("/roi/<id_>", methods=["PUT"])
def update_roi_region(id_):
    f, roi_type = check_roi_file(id_)
    if not f.exists():
        return error_response(400, "roi file does not exist")

    with f.open("w" if roi_type == "txt" else "wb") as f:
        f.write(f["roi"])

    return {
        "id": id_,
        "type": roi_type,
    }


def check_roi_file(id_):
    f = (roi_storage / id_).with_suffix(".bin")
    roi_type = "bin"
    if not f.exists():
        f = (roi_storage / id_).with_suffix(".txt")
        roi_type = "txt"
    return f, roi_type


@app.route("/roi/<id_>", methods=["GET"])
def get_roi_region(id_):
    f, roi_type = check_roi_file(id_)
    if not f.exists():
        return error_response(400, "roi file does not exist")

    with f.open("r" if roi_type == "txt" else "rb") as f:
        data = f.read()

    return jsonify(
        {
            "id": id_,
            "type": roi_type,
            "data": data
        }
    )


@app.route("/roi/<id_>", methods=["DELETE"])
def delete_roi_region(id_):

    f, roi_type = check_roi_file(id_)
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
    f, roi_type = check_roi_file(roi_id)
    if not f.exists():
        return error_response(400, "missing roi id")
    try:
        start_point = datetime.datetime.fromisoformat(data.get("start"))
    except (TypeError, ValueError) as e:
        return error_response(400, "Invalid start point" + str(e))
    try:
        duration = float(data.get("duration"))
    except TypeError:
        return error_response(400, "duration")
    a = app.task_queue.enqueue(
        "src.encoder.encode",
        f.with_suffix(f".{roi_type}"), start_point, duration, mkstemp()[1]
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
            "video_url": f"/video/{id_}.hevc"
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
    return Response(f.read_bytes(), mimetype="video/H265")