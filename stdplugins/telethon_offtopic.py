# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from asyncio import sleep, ensure_future

from telethon.tl.functions.channels import JoinChannelRequest
from telethon.errors import ChannelPrivateError, ChannelBannedError

# How often to fetch the full list of blocked users
REFETCH_TIME = 60 * 2
chat = "@telethonofftopic"


async def fetch_chats():
    while True:
        try:
            await borg(JoinChannelRequest(chat))
        except (ChannelBannedError, ChannelPrivateError):
            await sleep(REFETCH_TIME + 60)
        await sleep(REFETCH_TIME)


ensure_future(fetch_chats())
