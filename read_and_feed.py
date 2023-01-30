from datetime import datetime
from subprocess import Popen, PIPE
from time import sleep


def main():
    a = Popen(
        [
            'ffmpeg',
            '-f', 'rawvideo',
            '-pix_fmt', "yuv420p",
            '-s:v', "1920x1080",
            '-stream_loop', "-1",
            '-i', '/home/jovasa/Downloads/BasketballDrive_1920x1080_50_500.yuv',
            '-vf', rf"drawtext=fontsize=100:fontcolor=white:x=(w-text_w)/2:y=(h-text_h)/2:text=%{{n}}",
            '-f', "rawvideo",
            '-pix_fmt', "yuv420p",
            '-'

        ],
        stdout=PIPE
    )

    i = 0
    while True:
        start_time = datetime.now()
        b = Popen(
            [
                'ffmpeg',
                '-s:v', "1920x1080",
                '-f', 'rawvideo',
                '-pix_fmt', 'yuv420p',
                '-r', '30',
                '-i', 'pipe:.yuv',
                "-c:v", "libx264",
                f'media/output{i}.mp4',
                "-y"
            ],
            stdin=PIPE
        )
        for _ in range(30*10):
            f = a.stdout.read(int(1920 * 1080 * 1.5))
            b.stdin.write(f)
        b.stdin.close()
        i += 1
        end_time = datetime.now()
        sleep(10 - (end_time - start_time).total_seconds())
    a.stdout.close()


if __name__ == '__main__':
    main()
