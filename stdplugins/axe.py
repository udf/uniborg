# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import asyncio
import re

from telethon import events
from telethon.tl.types import Message

pattern = re.compile(r'(?i)^a+nd\b')


@borg.on(events.NewMessage)
async def and_my_axe(event):
    async def next_match(event):
        if pattern.match(event.raw_text):
            raise events.StopPropagation
        return True

    prev_event = None
    while pattern.match(event.raw_text):
        prev_message = getattr(prev_event, 'message', None)
        if event.is_reply:
            prev_message = await event.reply_message
            if not (isinstance(prev_message, Message)
                    and pattern.match(prev_message.message)):
                return

        if prev_message:
            if event.message.from_id != prev_message.from_id:
                await event.reply('and my axe!')
                return
            if event.is_reply:
                return

        prev_event = event
        event = await borg.await_event(
                events.NewMessage(chats=await event.input_chat), next_match
            )
