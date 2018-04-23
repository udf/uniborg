# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import os
import sys
import uuid
from telethon import events, utils
from telethon.tl import types, functions


# {name: (text, media)}
snips = storage.snips or {}


def remove_snip(name):
    if name in snips:
        text, media = snips[name]
        if media:
            try:
                os.remove(text)
            except Exception as e:
                print('failed to remove', snip, 'due to', e, file=sys.stderr)


@borg.on(events.NewMessage(pattern=r'.snip (\w+)'))
async def on_message(event):
    msg = await event.reply_message
    name = event.pattern_match.group(1)
    if msg:
        remove_snip(name)
        if msg.media:
            file = await borg.download_media(
                msg.media, os.path.join(storage._root, str(uuid.uuid4())))
            snips[name] = (file, True)
        else:
            snips[name] = (msg.message, False)
        storage.snips = snips
    elif name in snips:
        text, media = snips[name]
        if media:
            await borg.send_file(await event.input_chat, text)
        else:
            await borg.send_message(await event.input_chat, text)

    await event.delete()
