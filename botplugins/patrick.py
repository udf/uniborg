"""Ping!  Pong!

The bot will reply with the time it took to respond to your command.
Works in private only

pattern: `/ping$`
"""

from telethon import events
from datetime import datetime
from uniborg.util import cooldown, blacklist, chance


@borg.on(events.NewMessage(pattern=r"(?i)is\s+this\s+", func=lambda e: not e.is_private))
@chance(10)
async def patrick(event):
    blacklist = storage.blacklist or set()
    if event.chat_id in blacklist:
        return

    await event.reply("No, this is Patrick.")


@borg.on(borg.blacklist_plugin())
async def on_blacklist(event):
    storage.blacklist = await blacklist(event, storage.blacklist)
