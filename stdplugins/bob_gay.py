"""
bob pls
"""

import asyncio
from datetime import timedelta
from telethon import events
from telethon.tl import types


@borg.on(events.NewMessage(chats=151462131, incoming=True))
async def h(event):
    if not event.message.document:
        return
    if event.message.document.id == 541175087705893061:
        await event.delete(revoke=False)


@borg.on(events.NewMessage(
    pattern=r'(?i)(n(o|ein|ada)+[\s\u2063]+){1,50}([bdj]?(?:[uü]+|y\s?(?:o\s?u|e\s?w)))',
    chats=151462131,
    incoming=True,
    forwards=False
))
async def no_u(event):
    reply_msg = await event.get_reply_message()
    if reply_msg and event.message.date - reply_msg.date <= timedelta(seconds=5):
        return
    m = event.pattern_match
    msg = await event.reply('\u2063')
    await msg.edit(f'{m.group(1)}{m.string}'.lower())
