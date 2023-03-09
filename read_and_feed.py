import os
from datetime import datetime
from pathlib import Path
from subprocess import Popen, PIPE
from time import sleep
from dotenv import load_dotenv

load_dotenv()


def main():
    media_dir = (Path(__file__) / ".." / "media").resolve()
    media_dir.mkdir(exist_ok=True)
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
        stdout=PIPE
    )

    i = 0
    width, height = [int(x) for x in resolution.split("x")]
    while True:
        start_time = datetime.now()
        b = Popen(
            [
                'ffmpeg',
                '-s:v', resolution,
                '-f', 'rawvideo',
                '-pix_fmt', 'yuv420p',
                '-r', '30',
                '-i', 'pipe:.yuv',
                "-c:v", "libx264",
                str(media_dir / f'output{i}.mp4'),
                "-y"
            ],
            stdin=PIPE
        )
        for _ in range(30 * 10):
            f = a.stdout.read(int(width * height * 1.5))
            b.stdin.write(f)
        b.stdin.close()
        i += 1
        end_time = datetime.now()
        sleep(10 - (end_time - start_time).total_seconds())
    a.stdout.close()


if __name__ == '__main__':
    main()
