"""No, this is Patrick!

1 in 10 chance to respond to message starting with "Is this..." with "No, this is Patrick!

"""

from telethon import events
from datetime import datetime
from uniborg.util import cooldown, blacklist, chance


@borg.on(events.NewMessage(pattern=r"(?i)is\s+this\s+", func=lambda e: not e.is_private))
@cooldown(10)
@chance(2)
async def patrick(event):
    blacklist = storage.blacklist or set()
    if event.chat_id in blacklist:
        return

    await event.reply("No, this is Patrick.")


@borg.on(borg.blacklist_plugin())
async def on_blacklist(event):
    storage.blacklist = await blacklist(event, storage.blacklist)
