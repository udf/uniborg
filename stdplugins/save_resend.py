# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import asyncio
from telethon import events, utils
from telethon.tl import types
from telethon.tl.functions.messages import SaveDraftRequest


pending_messages = asyncio.Queue()
help_msg = None


@borg.on(events.NewMessage(chats=borg.uid, outgoing=False))
async def resend(event):
    if not help_msg:
        return
    await pending_messages.put(event.message)


@borg.on(events.NewMessage(chats=borg.uid, pattern=r'^\.sr$', outgoing=True))
async def toggle(event):
    global help_msg
    if help_msg:
        await help_msg.delete()
        help_msg = None
        await event.edit('Save resend has been disabled')
        await asyncio.sleep(3)
        await event.delete()
        return
    await event.edit('Save resend is enabled')
    help_msg = event.message


async def sender():
    global pending_messages
    while 1:
        m = await pending_messages.get()
        await borg.send_message('me', m)
        await borg.delete_messages('me', m)


def unload():
    if sender_loop:
        sender_loop.cancel()


sender_loop = asyncio.ensure_future(sender())