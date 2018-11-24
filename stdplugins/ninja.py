# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import asyncio

from telethon import events
from telethon.tl.types import InputPeerSelf
import telethon.utils

from uniborg import util


async def await_read(chat, message):
    if isinstance(chat, InputPeerSelf):
        return
    chat = telethon.utils.get_peer_id(chat)

    async def read_filter(read_event):
        return (read_event.chat_id == chat
                and read_event.is_read(message))
    fut = borg.await_event(events.MessageRead(inbox=False), read_filter)

    if await util.is_read(borg, chat, message):
        fut.cancel()
        return

    await fut


@borg.on(util.admin_cmd(r"^\.(del)(?:ete)?$"))
@borg.on(util.admin_cmd(r"^\.(edit)(?:\s+(.*))?$"))
async def delete(event):
    await event.delete()
    command = event.pattern_match.group(1)
    if command == 'edit':
        text = event.pattern_match.group(2)
        if not text:
            return
    target = await util.get_target_message(borg, event)
    if target:
        chat = await event.get_input_chat()
        await await_read(chat, target)
        await asyncio.sleep(.5)
        if command == 'edit':
            await borg.edit_message(chat, target, text)
        else:
            await borg.delete_messages(chat, target)
