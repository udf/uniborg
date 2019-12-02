# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import asyncio
from random import choice, randint
from telethon import events

group_id = 1146038279
user_id = 967435117
greetings = [
    'Hi', 'Hey', 'Hello', 'Sup', 'Yo'
]
sexy_things = [
    'TikTok', 'sex', 'hot sex', 'Alina', 'Eliza', 'Hebe', 'pedo', 'loli'
]

@borg.on(events.ChatAction(chats=group_id))
async def _(e):
    if not e.user_joined:
        return
    if user_id not in e.user_ids:
        return
    
    fut = borg.await_event(
        events.NewMessage(chats=group_id, from_users=user_id)
    )
    try:
        e = await asyncio.wait_for(fut, timeout=60 * 10)
        await asyncio.sleep(randint(30, 90))
        m = await e.reply(f'{choice(greetings)} Mono, want some {choice(sexy_things)}?')
        await borg.send_message(
            151462131,
            f'https://t.me/c/{group_id}/{m.id}'
        )
    except asyncio.TimeoutError:
        await borg.send_message(
            151462131,
            f'https://t.me/c/{group_id}/{e.action_message.id}'
        )
        pass
