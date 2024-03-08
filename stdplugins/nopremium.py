# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""
Deletes premium stickers and custom emoji
"""
from telethon import events
from telethon.tl.types import MessageMediaDocument

@borg.on(events.NewMessage(incoming=True))
async def _(event):
    media = event.message.media
    if not isinstance(media, MessageMediaDocument):
        return

    if media.document.mime_type != "application/x-tgsticker":
        return

    # This means the premium animation shouldn't be played so we allow it
    if media.nopremium:
        return

    # Why the fuck is it called video_thumbs
    # Supposedly this is the premium animation file
    if media.document.video_thumbs is not None:
        # Remove cancer
        await event.delete()
