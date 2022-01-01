# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""
Download images from pixiv links and post them directly
"""

from telethon import events

import aiohttp

# Unfortunately we can't guess the timestamp without parsing pixiv's HTML
#@borg.on(events.NewMessage(outgoing=True,
#    pattern=r"^https://www\.pixiv\.net/en/artworks/(?P<gallery>\d{8})#big_(?P<idx>\d+)$"))
@borg.on(events.NewMessage(outgoing=True,
    pattern=r"^https://i\.pximg\.net/img-original/img/(?P<path>\d{4}/\d{2}/\d{2}/\d{2}/\d{2}/\d{2}/(?P<gallery>\d{8})_p\d+)\.(?:png|jpg)$"))
@borg.on(events.NewMessage(outgoing=True,
    pattern=r"^https://i\.pximg\.net/c/\w+/img-master/img/(?P<path>\d{4}/\d{2}/\d{2}/\d{2}/\d{2}/\d{2}/(?P<gallery>\d{8})_p\d+)_master\d+\.jpg$"))
async def _(event):
    gallery_id = event.pattern_match.group("gallery")
    image_path = event.pattern_match.group("path")

    headers = { "Referer": "https://www.pixiv.net/" }
    async with aiohttp.ClientSession() as session:
        for ext in ["png", "jpg"]:
            image_url = f"https://i.pximg.net/img-original/img/{image_path}.{ext}"
            async with session.get(image_url, headers=headers) as response:
                if response.status == 404:
                    continue
                image = await response.read()
                break
        else:
            return
    await event.respond(
        f"https://www.pixiv.net/en/artworks/{gallery_id}",
        file=image
    )
    await event.delete()
