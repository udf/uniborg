"""
Swear Jar.  `.abl list of words` to add to blacklist, `.rbl list of words` to remove from blacklist, 
and .bl to see the blacklist
"""

import re
import asyncio
from telethon import events, utils
from telethon.tl import types
from telethon.tl.functions.messages import MarkDialogUnreadRequest
from telethon.events import StopPropagation


blacklist = storage.blacklist or {"fuck", "piss", "shit", "heck", "cunt", "bastard", "bitch", "damn"}


def is_swear(event):
    pattern = "|".join(blacklist)
    m = re.search(rf"(?i)\b({pattern})\b", event.text)

    if m:
        return True
    else:
        return False


@borg.on(events.NewMessage(outgoing=True, func=is_swear, forwards=False))
async def on_swear(event):
    await event.delete()

    reply_link = ""
    if event.is_group and event.is_reply:
        reply_link = f"**Replied to:**  https://t.me/c/{event.chat.id}/{event.reply_to_msg_id}\n\n"

    await borg(MarkDialogUnreadRequest(peer="me", unread=True))
    save_message = reply_link + event.text
    if not event.media:
        await borg.send_message("me", save_message)
        return
    await borg.send_file("me", event.media, caption=save_message)


@borg.on(borg.cmd(r"abl (.+)"))
async def add_blacklist(event):
    await event.delete()

    words = (event.pattern_match.group(1)).split()
    blacklist.update(words)

    storage.blacklist = blacklist
    raise StopPropagation


@borg.on(borg.cmd(r"rbl (.+)"))
async def remove_blacklist(event):
    await event.delete()

    words = (event.pattern_match.group(1)).split()
    blacklist.difference_update(words)

    storage.blacklist = blacklist


@borg.on(borg.cmd(r"bl"))
async def view_blacklist(event):
    await event.delete()

    await event.respond("**Blacklist:**\n• " + "\n• ".join(blacklist))
