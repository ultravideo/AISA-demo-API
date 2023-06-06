from sys import platform
import os
import sys
import cv2
import subprocess
from collections import deque
from datetime import datetime, timedelta
from pathlib import Path
from subprocess import Popen, PIPE, DEVNULL
from time import sleep
from dotenv import load_dotenv

load_dotenv()

def save_10_seconds_webcam(output_path, device):
    # Open the webcam
    cap = cv2.VideoCapture(0)  # Use 0 for the default camera

    # Check if the camera is opened correctly
    if not cap.isOpened():
        print("Failed to open the webcam")
        return

    # Get the frames per second (FPS) of the camera
    resolution = os.environ["RESOLUTION"] or "1920x1080"
    width, height = [int(x) for x in resolution.split("x")]
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
    fps = cap.get(cv2.CAP_PROP_FPS)
    # print(f'fps: {fps}')
    # cap.set(cv2.CAP_PROP_FPS, 30)


    # Calculate the number of frames to capture for 10 seconds
    num_frames = int(fps * 10)

    # Initialize variables
    frame_counter = 0
    video_frames = []

    while cap.isOpened() and frame_counter < num_frames:
        # Read a frame from the camera
        ret, frame = cap.read()

        if not ret:
            break

        # Add the frame to the list
        video_frames.append(frame)

        # Increment the frame counter
        frame_counter += 1

    # Release the camera
    cap.release()

    # Check if enough frames were captured
    if frame_counter < num_frames:
        print("Not enough frames available from the webcam")
        return

    # Get the width and height of the frames
    height, width, _ = video_frames[0].shape

    # Create a VideoWriter object to save the frames as an MP4 file
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    # Write the frames to the MP4 file
    for frame in video_frames:
        out.write(frame)

    # Release the VideoWriter
    out.release()


def main(camera_name="output", stream=""):
    media_dir = (Path(__file__) / ".." / "media" / camera_name).resolve()
    media_dir = Path(os.environ.get("MEDIA_DIR", media_dir))
    media_dir.mkdir(exist_ok=True, parents=True)
    for file in media_dir.glob("*"):
        file.unlink()
    resolution = os.environ["RESOLUTION"] or "1920x1080"
    # Example of looping a single file and drawing the frame number in the middle
    # [
    #     'ffmpeg',
    #     '-f', 'rawvideo',
    #     '-pix_fmt', "yuv420p",
    #     '-s:v', resolution,
    #     '-stream_loop', "-1",
    #     '-i', '/home/jovasa/Downloads/BasketballDrive_1920x1080_50_500.yuv',
    #     '-vf', rf"drawtext=fontsize=100:fontcolor=white:x=(w-text_w)/2:y=(h-text_h)/2:text=%{{n}}",
    #     '-f', "rawvideo",
    #     '-pix_fmt', "yuv420p",
    #     '-'
    # ]
    print(f"Stream {camera_name}: {stream}")
    if stream:
        a = None
    else:
        a = Popen(
            [
                'ffmpeg',
                '-f', 'lavfi',
                '-i', f'color=c=black:size={resolution}',
                '-vf', rf"drawtext=fontsize=100:fontcolor=white:x=(w-text_w)/2:y=(h-text_h)/2:text=%{{n}}",
                '-f', "rawvideo",
                '-pix_fmt', "yuv420p",
                '-'
            ],
            stdout=PIPE,
            stderr=DEVNULL
        )

    i = 0
    width, height = [int(x) for x in resolution.split("x")]
    segments = deque()
    while True:
        segment_start_time = datetime.utcnow()
        output_file = media_dir / f'output_{segment_start_time.isoformat()}.mp4'
        if a:
            b = Popen(
                [
                    'ffmpeg',
                    '-s:v', resolution,
                    '-f', 'rawvideo',
                    '-pix_fmt', 'yuv420p',
                    '-r', '30',
                    '-i', 'pipe:.yuv',
                    "-c:v", "libx264",
                    str(output_file),
                    "-y"
                ],
                stdin=PIPE,
                stderr=DEVNULL
            )
            for _ in range(30 * 10):
                f = a.stdout.read(int(width * height * 1.5))
                b.stdin.write(f)
            b.stdin.close()
        else:
            save_10_seconds_webcam(str(output_file), stream if platform != "darwin" else 0)

        i += 1
        segments.append(output_file)
        if len(segments) > 60:
            segment_to_remove = segments.popleft()
            segment_to_remove.unlink()
        segment_end_time = datetime.utcnow()
        # This is not needed if the input is from actual camera
        if (10 - (segment_end_time - segment_start_time).total_seconds()) > 0:
            sleep(10 - (segment_end_time - segment_start_time).total_seconds())

    if a:
        a.stdout.close()


if __name__ == '__main__':
    camera = sys.argv[1] if len(sys.argv) > 1 else "output"
    stream = sys.argv[2] if len(sys.argv) > 2 else "" 
    main(camera, stream)
