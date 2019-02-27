# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import asyncio

from telethon import events


_last_message = None


@borg.on(events.NewMessage(outgoing=True))
async def _(event):
    global _last_message
    _last_message = event.message


@borg.on(events.NewMessage(pattern=r"\.(fix)?reply", outgoing=True))
async def _(event):
    if not event.is_reply or not _last_message:
        return

    chat = await event.get_input_chat()
    await asyncio.wait([
        borg.delete_messages(chat, [event.id, _last_message.id]),
        borg.send_message(chat, _last_message, reply_to=event.reply_to_msg_id)
    ])
