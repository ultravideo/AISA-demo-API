import os
from collections import deque
from datetime import datetime, timedelta
from pathlib import Path
from subprocess import Popen, PIPE, DEVNULL
from time import sleep
from dotenv import load_dotenv

load_dotenv()


def main():
    media_dir = (Path(__file__) / ".." / "media").resolve()
    media_dir.mkdir(exist_ok=True)
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
        segment_start_time = datetime.now()
        output_file = media_dir / f'output_{segment_start_time.isoformat()}.mp4'
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
        i += 1
        segments.append(output_file)
        if len(segments) > 60:
            segment_to_remove = segments.popleft()
            segment_to_remove.unlink()
        segment_end_time = datetime.now()
        # This is not needed if the input is from actual camera
        sleep(10 - (segment_end_time - segment_start_time).total_seconds())
    a.stdout.close()


if __name__ == '__main__':
    main()
