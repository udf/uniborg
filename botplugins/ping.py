"""The bot will reply with the time it took to respond to your command.
Works in private only

pattern: `/ping$`
"""

from datetime import datetime
from telethon import events


# /ping
@borg.on(borg.cmd(r"ping$"))
async def ping_pong(event):
    if not event.is_private:
        return

    a = datetime.timestamp(datetime.now())
    message = await event.reply("**Pong!**")
    b = datetime.timestamp(datetime.now()) - a
    await message.edit(f"**Pong!**\nTook `{b:.3f}` seconds")
