# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""
Download images from pixiv links and post them directly
"""

from telethon import events

import aiohttp

@borg.on(events.NewMessage(outgoing=True,
    pattern=r"^https://i\.pximg\.net/img-original/img/\d{4}/\d{2}/\d{2}/\d{2}/\d{2}/\d{2}/(\d{8})_p\d+\.(?:png|jpg)$"))
async def _(event):
    image_url = event.pattern_match.group(0)
    gallery_id = event.pattern_match.group(1)

    headers = { "Referer": "https://www.pixiv.net/" }
    async with aiohttp.ClientSession() as session:
        async with session.get(image_url, headers=headers) as response:
            await event.respond(
                f"https://www.pixiv.net/en/artworks/{gallery_id}",
                file=await response.read()
            )
    await event.delete()
