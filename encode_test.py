import os
from datetime import datetime, timedelta
from pathlib import Path
from subprocess import Popen, PIPE, DEVNULL, check_call
from tempfile import mkstemp

import numpy as np

duration = 10.0

ffmpeg_cmd = [
    'ffmpeg', '-ss', '3.19912', 
    '-i', '/event_medias/output/output_2023-05-31T20:13:20.036643.mp4', 
    '-i', '/event_medias/output/output_2023-05-31T20:13:30.041467.mp4', 
    '-filter_complex', '[0:v][1:v]concat=n=2[outv]', 
    '-map', '[outv]', '-t', f'{duration}', 
    '-f', 'rawvideo', 
    '-pix_fmt', 'yuv420p', '-'
]

ffmpeg_handle = Popen(
    ffmpeg_cmd,
    stdout=PIPE,
    # stderr=DEVNULL
)

resolution = "480x360"
roi_file = None
out_file = "/event_medias/kavazaar_test"
out_path = "/event_medias/kavazaar_test.mp4"


encode_command = [
    "kvazaar",
    "--input-fps", "30",
    "-i", "-",
    "--input-res", resolution,
    "--preset", "ultrafast",
    "--qp", "27" if roi_file is not None else "27",
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

    print(a, end="")

kvazaar_handle.wait()
print(f"Kvazaar done {str(out_file)}")

check_call(
    [
        "MP4Box",
        "-add", str(out_file),
        "-new", str(out_path)
    ]
)
