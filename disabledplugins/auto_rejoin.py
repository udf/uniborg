# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from asyncio import sleep, ensure_future

from telethon import events
from telethon.tl.functions.messages import SaveDraftRequest
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.errors import ChannelPrivateError, ChannelBannedError


# How often to attempt to rejoin
REFETCH_TIME = 90
chat = "@telethonofftopic"


@borg.on(events.NewMessage(chats=chat))
async def last_msg_draft(event):
    last_msg = event.id
    storage.last_msg = last_msg


@borg.on(events.ChatAction(chats=chat, func=lambda e: e.user_joined))
async def joined(event):
    if event.user_id != borg.uid:
        return
    last_msg = storage.last_msg or 0
    await borg(SaveDraftRequest(peer=chat, message="", reply_to_msg_id=last_msg))


async def fetch_chats():
    while True:
        try:
            await borg(JoinChannelRequest(chat))
        except (ChannelBannedError, ChannelPrivateError):
            logger.info("Still banned")
            await sleep(REFETCH_TIME + 60)
        await sleep(REFETCH_TIME)


ensure_future(fetch_chats())
