# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from telethon import events

@borg.on(events.NewMessage(pattern=r"\.all", outgoing=True))
async def _(event):
    if event.forward:
        return
    await event.delete()
    mentions = "@all"
    async for x in borg.iter_participants(await event.input_chat, 100):
        mentions += f"[\u2063](tg://user?id={x.id})"
    await event.respond(mentions)
