# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""
Download images from pixiv links and post them directly
"""

import asyncio
import io
import os
import tempfile
import zipfile

from telethon import events
from telethon import types

import aiohttp

auth_cookie = storage.auth_cookie or ""

# This is required for the pixiv CDN to actually give us the images
cdn_headers = { "Referer": "https://www.pixiv.net/" }

image_loading_url = \
    "https://cdn.donmai.us/original/e8/34/__ptilopsis_arknights_drawn_by_kuhl_notes__e83431cd42e85cde0d7f67b35e6022d7.png"
ugoira_loading_url = \
    "https://cdn.donmai.us/original/0d/e4/__ptilopsis_arknights_drawn_by_kuhl_notes__0de44fb72977db0c0594244cdc10ee61.mp4"

@borg.on(borg.cmd(r"pixiv_auth_cookie", r"(?s)\s+(?P<args>\w+)"))
async def _(event):
    if event.fwd_from:
        return
    await event.delete()

    global auth_cookie
    auth_cookie = event.pattern_match["args"]
    storage.auth_cookie = auth_cookie

# Web gallery links, including those referring to a specific image
@borg.on(events.NewMessage(outgoing=True,
    pattern=r"^https?://www\.pixiv\.net/(?:\w+/)?artworks/(?P<gallery>\d{6,9})(?:#big_(?P<index>\d+)|#manga|#range(?P<range>\d+-\d+))?$"))
@borg.on(events.NewMessage(outgoing=True,
    pattern=r"^https?://www\.pixiv\.net/member_illust.php?.*illust_id=(?P<gallery>\d{6,9})"))
# Direct links to an image on the CDN
@borg.on(events.NewMessage(outgoing=True,
    pattern=r"^https?://i\.pximg\.net/.*/(?P<gallery>\d{6,9})_p(?P<index>\d+)(?:\w+)?\.(?:png|jpg)$"))
async def _(event):
    if event.fwd_from:
        return

    if event.media and not isinstance(event.media, types.MessageMediaWebPage):
        return

    gallery_id = event.pattern_match.group("gallery")
    try:
        image_index = event.pattern_match.group("index")
    except IndexError:
        image_index = None
    try:
        subrange = event.pattern_match.group("range")
    except IndexError:
        subrange = None
    logger.info(f"Processing pixiv gallery #{gallery_id}, image #{image_index}, range {subrange}")

    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"https://www.pixiv.net/ajax/illust/{gallery_id}/ugoira_meta",
            headers={ "User-Agent": "Mozilla/5.0" },
            cookies={ "PHPSESSID": auth_cookie },
        ) as response:
            if response.status != 404:
                await ugoira(event, gallery_id, session, await response.json())
                return

        async with session.get(
            f"https://www.pixiv.net/ajax/illust/{gallery_id}/pages",
            headers={ "User-Agent": "Mozilla/5.0" },
            cookies={ "PHPSESSID": auth_cookie },
        ) as response:
            index = await response.json()
        if index["error"]:
            logger.warn(index["message"])
            return
        urls = [i["urls"]["regular"] for i in index["body"]]
        total = len(urls)

        if subrange is not None:
            # If a range was specified, send the entire range
            start, end = subrange.split("-")
            urls = urls[int(start):int(end) + 1]
        elif image_index is not None:
            # If a specific image was linked, only send that
            urls = [urls[int(image_index)]]
        else:
            # Limit to 10 images (a single Telegram album)
            urls = urls[:10]

        more = total - len(urls)
        more = f"({more} more)" if more > 0 else ""
        loading = await borg.upload_file("loading.jpg")
        messages = await event.respond(
            f"https://www.pixiv.net/artworks/{gallery_id} {more}",
            file=[loading] * len(urls),
            reply_to=event.message.reply_to_msg_id
        )
        await event.delete()

        for u, m in zip(urls, messages):
            asyncio.create_task(m.edit(file=u))

async def ugoira(event, gallery_id, session, metadata):
    return

    if metadata["error"]:
        logger.warn(metadata["message"])
        return

    message = await event.respond(
        f"https://www.pixiv.net/artworks/{gallery_id}",
        file=ugoira_loading_url,
        reply_to=event.message.reply_to_msg_id
    )
    await event.delete()

    metadata = metadata["body"]
    with tempfile.TemporaryDirectory(prefix="ugoira.") as tmpdir:
        async with session.get(metadata["src"], headers=cdn_headers) as response:
            with io.BytesIO(await response.read()) as bio:
                with zipfile.ZipFile(bio) as zf:
                    zf.extractall(tmpdir)

        seqfile = os.path.join(tmpdir, "sequence.txt")
        with open(seqfile, "w") as sf:
            for frame in metadata["frames"]:
                sf.write(f"file {frame['file']}\n")
                sf.write(f"duration {frame['delay'] / 1000}\n")

            #  Due to a quirk, the last image has to be specified twice
            # - the 2nd time without any duration directive
            # (https://trac.ffmpeg.org/wiki/Slideshow)
            last_frame = metadata["frames"][-1]
            sf.write(f"file {last_frame['file']}\n")

        outfile = os.path.join(tmpdir, "ugoira.mp4")
        proc = await asyncio.create_subprocess_exec(
            "ffmpeg",
            "-y",
            "-f", "concat",
            "-i", seqfile,
            "-c:v", "libx264",
            "-vsync", "vfr",
            "-pix_fmt", "yuv420p",
            # Ensure resolution is divisible by 2
            "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2",
            outfile,
        )
        await proc.wait()

        await message.edit(file=outfile)
