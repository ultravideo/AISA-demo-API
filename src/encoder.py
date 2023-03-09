import os
from pathlib import Path
from subprocess import Popen, PIPE, DEVNULL
from rq import get_current_job
from dotenv import load_dotenv

from src import video_storage

load_dotenv()


def ffmpeg_concat_and_pipe_partial_videos(time, duration):
    current_segment = int(time // 10)
    total_time = (time % 10)
    inputs = ["ffmpeg", f"-ss", f"{total_time}", "-i", f"media/output{current_segment}.mp4"]
    concat = [f"[0:v]"]
    total_time = 10 - total_time

    while total_time < duration:
        current_segment += 1
        current_segment %= 60
        concat.append(f"[{len(concat)}:v]")
        inputs.extend(["-i", f"media/output{current_segment}.mp4"])
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


def encode(roi_file, start_time, duration, out_file):
    job = get_current_job()
    job.meta["file"] = out_file
    ffmpeg_cmd = ffmpeg_concat_and_pipe_partial_videos(start_time, duration)
    job_get_id = job.get_id()
    ffmpeg_handle = Popen(
        ffmpeg_cmd,
        stdout=PIPE,
        stderr=DEVNULL
    )
    resolution = os.environ["RESOLUTION"] or "1920x1080"
    kvazaar_handle = Popen(
        [
            "kvazaar",
            "--input-fps", "30",
            "-i", "-",
            "--input-res", resolution,
            "--roi", roi_file,
            "--preset", "medium",
            "--qp", "32",
            "-o", out_file
        ],
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

    out = (video_storage / job_get_id).with_suffix(".hevc")
    Path(out_file).rename(out)
