import asyncio
from telethon import events
from telethon.tl import types
import re

@borg.on(events.NewMessage(pattern=re.compile(r"^bar$"), chats=1040270887))
async def on_bar(event):
    if event.from_id == 151462131:
        return
    await event.reply("foo")
