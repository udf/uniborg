"""File to Photo

When an image file is sent to the bot, it will respond with a compressed preview of the file.
It will only respond to image files under 15 MB (15000000 bytes).
"""

import asyncio
from io import BytesIO
import concurrent.futures
from uniborg.util import cooldown, downscale
from telethon import events, errors, functions, types

executor = concurrent.futures.ThreadPoolExecutor()

@borg.on(events.NewMessage(func=lambda e: e.is_private))
async def on_photo(event):
    try:
        msg = event.message
        image = msg.media.document
    except AttributeError:
        return

    if "image" not in image.mime_type:
        return

    if image.size > 15 * 1000 * 1000: # 15 MB
        await event.reply("Image too large!  It must be under 15 MB.")
        return

    async with borg.action(event.sender_id, "photo"):
        f = await event.download_media(file=BytesIO())
        f.seek(0)
        im, resolution = await downscale(f)
        # im, resolution = await asyncio.get_running_loop().run_in_executor(
        #     executor,
        #     lambda: downscale(f)
        # )
        im.seek(0)
        dimensions = f"`{resolution[0]}x{resolution[1]}`"

        try:
            im.name = "image.png"
            await event.reply(message=dimensions, file=im)
        except errors.rpcerrorlist.PhotoInvalidDimensionsError:
            await event.reply(f"The photo's dimensions ({dimensions}) are not supported by Telegram.")
