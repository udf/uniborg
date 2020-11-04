# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""
Show information about the chat or replied user
"""
import datetime
import html
import time

from telethon import events
from telethon import utils
from telethon.tl import types, functions


def get_who_string(who, rank=None):
    who_string = html.escape(utils.get_display_name(who))
    if rank is not None:
        who_string += f' <i>"{html.escape(rank)}"</i>'
    if isinstance(who, (types.User, types.Channel)) and who.username:
        who_string += f" <i>(@{who.username})</i>"
    who_string += f", <a href='tg://user?id={who.id}'>#{who.id}</a>"
    return who_string


@borg.on(events.NewMessage(pattern=r"\.members", outgoing=True))
async def _(event):
    last = 0
    index = 0
    members = []

    it = borg.iter_participants(event.chat_id)
    async for member in it:
        index += 1
        now = time.time()
        if now - last > 0.5:
            last = now
            await event.edit(f'counting member stats ({index / it.total:.2%})…')

        messages = await borg.get_messages(
            event.chat_id,
            from_user=member,
            limit=0
        )
        members.append((
            messages.total,
            f"{messages.total} - {get_who_string(member)}"
        ))
    members = (
        m[1] for m in sorted(members, key=lambda m: m[0], reverse=True)
    )

    await event.edit("\n".join(members), parse_mode='html')


@borg.on(events.NewMessage(pattern=r"\.active_members", outgoing=True))
async def _(event):
    members = []
    async for member in borg.iter_participants(event.chat_id):
        messages = await borg.get_messages(
            event.chat_id,
            from_user=member,
            limit=1
        )
        date = (messages[0].date if messages
            else datetime.datetime.fromtimestamp(0, tz=datetime.timezone.utc))
        members.append((
            date,
            f"{date:%Y-%m-%d} - {get_who_string(member)}"
        ))
    members = (
        m[1] for m in sorted(members, key=lambda m: m[0], reverse=True)
    )

    await event.edit("\n".join(members), parse_mode='html')
