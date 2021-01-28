"""v.redd.it Downloader

Downloads SFW `v.reddi.it` videos, and sends them back as a video.
"""

import os
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
import re
from telethon import events
from uniborg.util import downscale, edit_blacklist


executor = concurrent.futures.ThreadPoolExecutor()


ytdl_opts = {
    "format": "best/bestvideo+bestaudio",
    "quiet": "true"
}

async def generator(size=randint(8,16)):
    chars = string.ascii_letters + string.digits
    return "".join(choice(chars) for _ in range(size))


def download(url):
    with youtube_dl.YoutubeDL(ytdl_opts) as ytdl:
        f = ytdl.extract_info(url)
    return f


def compress(f, output, out_thumb):
    ff = FFmpeg(
        inputs={f: None},
        outputs={
            output: "-c:v libx264 -pix_fmt yuv420p -b:v 3M -vf 'scale=trunc(iw/2)*2:trunc(ih/2)*2'",
            out_thumb: "-ss 00:00:0.500 -vframes 1"
        }
    )
    print("compressing")
    ff.run(stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    print("compressed")



async def vreddit(event, match):
    vids = []

    check = await event.reply(f"Checking")
    for m in match:
        await check.edit(f"Checking {match.index(m)+1}/{len(match)}")
        url = requests.get(m).url
        post_json = requests.get(url + ".json", headers={'User-Agent': f"{await generator()}"}).json()
        over_18 = post_json[0]['data']['children'][0]['data']['over_18']

        if over_18 and event.is_private or not over_18:
            vids.append(m)
        elif over_18 and not event.is_private:
            me = (await event.client.get_me()).username
            sub = re.sub(r"(?:https?\://)?v\.redd\.it/", "", m)

            link = f"t.me/{me}?start=vreddit_{sub}"
            await event.reply(f"[NSFW: click to view]({link})", link_preview=False)

    await check.delete()


    for v in vids:
        dl_msg = await event.reply(f"Downloading... {match.index(v)+1}/{len(vids)}")

        try:
            now = str(time())

            ytdl_opts["outtmpl"] = f"%(title)s{now}.%(ext)s"
            f = await asyncio.get_event_loop().run_in_executor(
                executor,
                lambda: download(v)
            )

            file_name = f"{f['title']}{now}.mp4"
            outfile = "o_" + file_name
            thumbbig = outfile + ".jpg"

            await asyncio.get_event_loop().run_in_executor(
                executor,
                lambda: compress(file_name, outfile, thumbbig)
            )
            thumb, res = await downscale(thumbbig, 320, 320, format="JPEG")
            thumb.seek(0)

            async with event.client.action(event.chat, "video"):
                thumb.name = "image.jpg"
                # TODO:
                ## Get thumbnails working - i have no idea how
                await event.client.send_file(event.chat_id, file=outfile, caption=v, reply_to=event.id, thumb=thumb, supports_streaming=True)
        except:
            pass

        await dl_msg.delete()
        os.remove(file_name)
        os.remove(outfile)
        os.remove(thumbbig)



@borg.on(events.NewMessage(pattern=r"/start vreddit_(\w+)$"))
async def on_start_vid(event):
    link = ["https://v.redd.it/" + event.pattern_match.group(1)]
    await vreddit(event, link)


@borg.on(events.NewMessage(pattern=re.compile(
                                    r"(?i)(?:^|\s)((?:https?\://)?v\.redd\.it/\w+)").findall
                                    ))
async def on_vreddit(event):
    blacklist = storage.blacklist or set()
    if event.chat_id in blacklist:
        return

    # Check if the message is forwarded from self
    fwd = event.forward

    if fwd and (await fwd.get_sender()).is_self:
        return
    else:
        await vreddit(event, event.pattern_match)


@borg.on(borg.admin_cmd(r"(r)?blacklist", r"(?P<shortname>\w+)"))
async def blacklist(event):
    m = event.pattern_match
    shortname = m["shortname"]

    if shortname not in __file__:
        return

    storage.blacklist = edit_blacklist(event.chat_id, storage.blacklist, m.group(1))
    await event.reply("Updated blacklist.")
