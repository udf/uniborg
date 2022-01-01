# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""
Download images from pixiv links and post them directly
"""

import asyncio

from telethon import events

import aiohttp

# Web gallery links, including those referring to a specific image
@borg.on(events.NewMessage(outgoing=True,
    pattern=r"^https://www\.pixiv\.net/(?:\w+)/artworks/(?P<gallery>\d{8})(?:#big_(?P<index>\d+))?$"))
# Direct links to an image on the CDN
@borg.on(events.NewMessage(outgoing=True,
    pattern=r"^https://i\.pximg\.net/.*/(?P<gallery>\d{8})_p(?P<index>\d+)(?:\w+)?\.(?:png|jpg)$"))
async def _(event):
    gallery_id = event.pattern_match.group("gallery")
    image_index = event.pattern_match.group("index")

    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://www.pixiv.net/ajax/illust/{gallery_id}/pages") as response:
            index = await response.json()
        if index["error"]:
            # TODO error message?
            return
        urls = [i["urls"]["regular"] for i in index["body"]]
        total = len(urls)

        # If a specific image was linked, only send that
        if image_index is not None:
            urls = [urls[int(image_index)]]

        # Limit to 10 images (a single Telegram album)
        urls = urls[:10]

        more = total - len(urls)
        more = f"({more} more)" if more > 0 else ""
        spinner = await borg.upload_file("spinner.jpg")
        messages = await event.respond(
            f"https://www.pixiv.net/en/artworks/{gallery_id} {more}",
            file=[spinner] * len(urls)
        )
        await event.delete()

        # This is required for the pixiv CDN to actually give us the images
        headers = { "Referer": "https://www.pixiv.net/" }
        for u, m in zip(urls, messages):
            async with session.get(u, headers=headers) as response:
                file = await response.read()
                # Upload the image asynchronously so we can keep downloading
                # concurrently
                asyncio.create_task(m.edit(file=file))
