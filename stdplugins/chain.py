# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""
Counts how long a reply .chain is
"""
from collections import defaultdict

from telethon import events
from telethon.tl.functions.messages import SaveDraftRequest

def intify(d):
    for k, v in d.items():
        if isinstance(v, dict):
            v = dict(intify(v))
        yield int(k), v

global_cache = defaultdict(lambda: {}, intify(storage.cache or {}))

@borg.on(events.NewMessage(pattern=r"\.chain", outgoing=True))
async def _(event):
    cache = global_cache[event.chat_id]

    message = event.reply_to_msg_id
    count = 0
    while message is not None:
        reply = cache.get(message, -1)
        if reply == -1:
            reply = None
            if m := await borg.get_messages(event.chat_id, ids=message):
                reply = m.reply_to_msg_id
                cache[message] = reply
                if len(cache) % 10 == 0:
                    await event.edit(f"Counting... ({len(cache)} cached entries)")

        if reply is None:
            await borg(SaveDraftRequest(
                await event.get_input_chat(),
                "",
                reply_to_msg_id=message
            ))

        message = reply
        count += 1

    if count:
        storage.cache = global_cache
    await event.edit(f"Chain length: {count}")
