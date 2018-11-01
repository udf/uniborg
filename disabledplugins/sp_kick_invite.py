# kicks people who join a group by invite

import asyncio
from telethon import events

from telethon.tl.functions.channels import EditBannedRequest
from telethon.tl.types import ChannelBannedRights

import time

channel_id = 1252035294


@borg.on(events.ChatAction(chats=channel_id))
async def on_join(event):
    if event.user_joined:
        await borg(
            EditBannedRequest(
                channel=channel_id,
                user_id=await event.get_user(),
                banned_rights=ChannelBannedRights(
                   time.time() + 60,
                   True, True, True, True, True, True, True, True
                )
            )
        )
