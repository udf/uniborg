# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""
Reply with .fixreply to adjust your last message's reply
"""
import asyncio

from telethon import events

chat = "@telethonofftopic"
uid = 234480941


@borg.on(events.NewMessage(chats=chat,
    pattern=r"/(yee+t|purge)",
    func=lambda e: e.sender_id == uid and e.mentioned))
async def meme(event):
    # await event.reply(file=f)
    await event.reply("You can't win, Twit. \
    \nIf you strike me down I shall become more powerful than you can possibly imagine.")
