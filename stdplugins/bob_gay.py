"""
bob pls
"""

import asyncio
from random import choice
from datetime import timedelta
from telethon import events
from telethon.tl import types

from api_key import blanks


CHAT_ID = 151462131
MSG_IDS = set()


def insert_blanks(s):
    return ''.join(c + choice((choice(blanks), '')) for c in s)


@borg.on(events.NewMessage(chats=CHAT_ID, incoming=True))
async def h(event):
    if not event.message.document:
        return
    if event.message.document.id == 541175087705893061:
        await event.delete(revoke=False)


@borg.on(events.NewMessage(
    pattern=r'(?i)(n(o|ein|ada)+[\s\u2063]+){1,50}([bdj]?(?:[uü]+|y\s?(?:o\s?u|e\s?w)))',
    chats=CHAT_ID,
    incoming=True,
    forwards=False
))
async def no_u(event):
    reply_msg = await event.get_reply_message()
    if reply_msg and reply_msg.id in MSG_IDS:
        await event.delete(revoke=True)
        return
    if reply_msg and event.message.date - reply_msg.date <= timedelta(seconds=5):
        return
    m = event.pattern_match
    msg = await event.reply(insert_blanks(f'{m.group(1)}{m.string}'.lower()))
    MSG_IDS.add(msg.id)
