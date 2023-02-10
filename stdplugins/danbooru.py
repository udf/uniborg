# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""
Download images from danbooru links and post them directly
"""

import re

from telethon import events
from telethon import types
from telethon.errors.rpcerrorlist import MediaEmptyError

import aiohttp

def fix_tag_string(tag_string):
    tag_string = re.sub(r"[^\w ]", "_", tag_string)
    return " ".join("#" + tag for tag in tag_string.split())

@borg.on(events.NewMessage(outgoing=True,
    pattern=r"^https?://danbooru\.donmai\.us/posts/(?P<id>\d+)"))
async def _(event):
    if event.fwd_from:
        return

    if event.media and not isinstance(event.media, types.MessageMediaWebPage):
        return

    post_id = event.pattern_match.group("id")
    logger.info(f"Processing danbooru post #{post_id}")

    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"https://danbooru.donmai.us/posts/{post_id}.json",
        ) as response:
            meta = await response.json()
            if response.status != 200 or not meta.get("success", True):
                error = meta.get("error")
                message = meta.get("message")
                logger.warn(
                    f"Error while processing danbooru post #{post_id}: "
                    f"status={response.status}, "
                    f"error={error}, message={message}"
                )
                return

        url = meta["large_file_url"]
        message_text = f"https://danbooru.donmai.us/posts/{post_id}"
        if source := meta.get("tag_string_copyright"):
            message_text += f"\nSource: {fix_tag_string(source)}"
        if chars := meta.get("tag_string_character"):
            message_text += f"\nCharacters: {fix_tag_string(chars)}"
        if artist := meta.get("tag_string_artist"):
            message_text += f"\nArtist: {fix_tag_string(artist)}"

        try:
            await event.respond(
                message_text,
                file=url,
                reply_to=event.message.reply_to_msg_id,
            )
        except:
            message_text += "\n(Telegram rejected the upload)"
            await event.edit(message_text)
        else:
            await event.delete()
