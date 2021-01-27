"""
Tag all admins with `.admins?`
"""

import asyncio
from telethon import events
from telethon.tl.types import ChannelParticipantsAdmins


@borg.on(events.NewMessage(pattern=r"[\.@]admins?"))
async def _(event):
    reply_msg = "@admin"

    async for a in borg.iter_participants(event.chat_id, filter=ChannelParticipantsAdmins):
        reply_msg += f"[\u2063](tg://user?id={a.id})"

    await event.respond(reply_msg, reply_to=event.reply_to_msg_id)
    await event.delete()