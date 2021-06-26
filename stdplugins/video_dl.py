"""Video Downloader

Will download videos in messages, and upload them to saved messages
"""

import os
import re
import string
import asyncio
import requests
import subprocess
import youtube_dl
from time import time
from io import BytesIO
from ffmpy import FFmpeg
from random import randint, choice
import concurrent.futures
from telethon import events
from uniborg.util import downscale


executor = concurrent.futures.ThreadPoolExecutor()


# ytdl_opts = {
#     "format": "best/bestvideo+bestaudio",
#     "quiet": "true"
# }


ytdl_opts = [
    "youtube-dl",
    "-f",
    "best/bestvideo+bestaudio",
]

def generator(size=randint(8,16)):
    chars = string.ascii_letters + string.digits
    return "".join(choice(chars) for _ in range(size))


def download(url, file_name):
    # with youtube_dl.YoutubeDL(ytdl_opts) as ytdl:
    #     f = ytdl.download(url)
    opts = ytdl_opts
    opts += ["-o", file_name, url]
    print(opts)
    f = subprocess.run(opts, capture_output=True)
    return f


def compress(f, output, out_thumb):
    ff = FFmpeg(
        inputs={f: None},
        outputs={
            output: "-c:v libx264 -pix_fmt yuv420p -crf 25 -vf 'scale=trunc(iw/2)*2:trunc(ih/2)*2'",
            out_thumb: "-ss 00:00:0.500 -vframes 1"
        }
    )
    print("compressing")
    ff.run(stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    print("compressed")


@borg.on(borg.cmd(r"dl(\s+((http|www).+))?"))
async def on_command(event):
    await event.delete()

    m = event.pattern_match
    video = m.group(2)

    if not m.group(2):
        reply = (await event.get_reply_message()).raw_text
        video = re.search(r"((http|www).+)(\s|$)", reply).group(0)

    print(video)

    now = str(time())

    # ytdl_opts["outtmpl"] = f"{generator}_{now}.%(ext)s"
    
    file_name = f"{generator()}{now}.mp4"
    f = await asyncio.get_event_loop().run_in_executor(
        executor,
        lambda: download(video, file_name)
    )

    outfile = "o_" + file_name
    thumbbig = outfile + ".jpg"

    await asyncio.get_event_loop().run_in_executor(
        executor,
        lambda: compress(file_name, outfile, thumbbig)
    )
    thumb, res = await downscale(thumbbig, 320, 320, format="JPEG")
    thumb.seek(0)

    async with borg.action(event.chat_id, "video") as action:
        thumb.name = "image.jpg"
        await borg.send_file(
            "me", file=outfile, caption=video, thumb=thumb, supports_streaming=True,
            progress_callback=action.progress
        )

    os.remove(file_name)
    os.remove(outfile)
    os.remove(thumbbig)

