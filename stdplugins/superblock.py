# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import asyncio

from telethon import events, utils
import telethon.tl.functions as tlf
from telethon.tl.types import InputPeerChannel, UpdatePeerBlocked
from telethon.tl.functions.contacts import GetBlockedRequest


# How often to fetch the full list of blocked users
REFETCH_TIME = 60

blocked_user_ids = set()


@borg.on(events.NewMessage(incoming=True, func=lambda e: e.message.mentioned))
async def on_mentioned(event):
    if not event.message.from_id:  # Channel messages don't have a from_id
        return
    if event.from_id not in blocked_user_ids:
        return

    peer = await borg.get_input_entity(event.chat_id)
    if isinstance(peer, InputPeerChannel):
        o = tlf.channels.ReadMessageContentsRequest(peer, [event.message.id])
    else:
        o = tlf.messages.ReadMessageContentsRequest([event.message.id])
    await borg(o)


@borg.on(events.Raw(types=UpdatePeerBlocked))
async def on_blocked(event):
    id = utils.get_peer_id(event.peer_id)
    if event.blocked:
        blocked_user_ids.add(id)
    else:
        blocked_user_ids.discard(id)


async def fetch_blocked_users():
    global blocked_user_ids
    while 1:
        offset = 0
        blocked_ids = set()
        while 1:
            blocked = await borg(GetBlockedRequest(offset=offset, limit=100))
            offset += 100
            for peer in blocked.blocked:
                blocked_ids.add(utils.get_peer_id(peer.peer_id))
            if not blocked.blocked:
                break
        blocked_user_ids = blocked_ids
        await asyncio.sleep(REFETCH_TIME)


asyncio.ensure_future(fetch_blocked_users())
