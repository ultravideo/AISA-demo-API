import os
from datetime import datetime, timedelta
from pathlib import Path
from subprocess import Popen, PIPE, DEVNULL, check_call
from tempfile import mkstemp

import numpy as np
from rq import get_current_job
from dotenv import load_dotenv

from src import video_storage, roi_storage, models, db, app, api

load_dotenv()


def ffmpeg_concat_and_pipe_partial_videos(time, duration, camera):
    segments = sorted(os.listdir((Path(__file__) / ".." / ".." / "media" / camera).resolve()))
    i = 0
    current_segment = None
    segment_start = None
    start_time = time - timedelta(seconds=duration)
    for i, v in enumerate(segments):
        r = datetime.fromisoformat(v.split("_")[1][:-4])
        if r >= start_time:
            break
        else:
            current_segment = v
            segment_start = r

    seek = start_time - segment_start
    inputs = ["ffmpeg", f"-ss", f"{seek.seconds}.{seek.microseconds}", "-i", f"media/{camera}/{current_segment}"]
    concat = [f"[0:v]"]
    total_time = 10 - seek.seconds - seek.microseconds / 1e7
    print(f"segments: {segments}")

    while total_time < duration and i < len(segments):
        i += 1
        concat.append(f"[{len(concat)}:v]")
        inputs.extend(["-i", f"media/{camera}/{segments[i]}"])
        total_time += 10

    concat.append(f"concat=n={len(concat)}[outv]")
    inputs.extend(
        ["-filter_complex", "".join(concat),
         "-map", "[outv]",
         "-t", str(duration),
         "-f", "rawvideo",
         "-pix_fmt", "yuv420p",
         "-"]
    )
    return inputs


def preprocess_roi(f):
    data = np.load(roi_storage / f, allow_pickle=True)
    data *= -10
    handle, name = mkstemp()
    file = os.fdopen(handle, "w")
    file.write(f"{data.shape[1]} {data.shape[0]}\n")
    for line in data:
        print(file=file, *line, sep=" ")
    return name


def encode(roi_file, start_time, duration, out_file, camera, out_path):
    job = get_current_job()
    job.meta["file"] = out_file
    ffmpeg_cmd = ffmpeg_concat_and_pipe_partial_videos(start_time, duration, camera)
    job_get_id = job.get_id()

    if roi_file is not None:
        roi_file = preprocess_roi(roi_file)

    print(f"ffmpeg cmd: {ffmpeg_cmd}")
    ffmpeg_handle = Popen(
        ffmpeg_cmd,
        stdout=PIPE,
        stderr=DEVNULL
    )
    resolution = os.environ["RESOLUTION"] or "1920x1080"
    encode_command = [
        "kvazaar",
        "--input-fps", "30",
        "-i", "-",
        "--input-res", resolution,
        "--preset", "ultrafast",
        "--qp", "37" if roi_file is not None else "27",
        "-o", str(out_file),
    ]
    if roi_file is not None:
        encode_command.extend([
            "--roi", roi_file,
        ])

    kvazaar_handle = Popen(
        encode_command,
        stdin=ffmpeg_handle.stdout,
        stderr=PIPE,
    )
    frames_encoded = 0
    total_frames = duration * 30
    for line in kvazaar_handle.stderr:
        a = line.decode()
        if a.startswith("POC"):
            frames_encoded += 1
        job.meta["progress"] = 100 * frames_encoded / total_frames
        job.save_meta()

    job.meta["progress"] = 100
    job.save_meta()

    kvazaar_handle.wait()

    print(f"Kvazaar done {str(out_file)}")

    if out_path is None:
        out_path = (video_storage / job_get_id).with_suffix(".mp4")
    check_call(
        [
            "MP4Box",
            "-add", str(out_file),
            "-new", str(out_path)
        ]
    )

    with app.app_context():
        r = models.Encoding(id=job_get_id, out_path=str(out_path))
        db.session.add(r)
        db.session.commit()

    if roi_file is not None:
        roi_file = Path(roi_file)
        roi_file.unlink()
