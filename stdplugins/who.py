# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""
Show information about the chat or replied user using `.who`, `.members`, and `.active_members`
"""
import datetime
import html
import time

from telethon import events
from telethon import utils
from telethon.tl import types, functions


def get_who_string(who, who_id=None, rank=None):
    if who_id is None or isinstance(who, types.User):
        who_id = who.id

    who_string = f"<a href='tg://user?id={who.id}'>"
    who_string += html.escape(utils.get_display_name(who)) + "</a>"

    if rank is not None:
        who_string += f' <i>"{html.escape(rank)}"</i>'
    if isinstance(who, (types.User, types.Channel)) and who.username:
        who_string += f" <i>(@{who.username})</i>"

    who_string += f", <code>{who_id}</code>"
    return who_string


@borg.on(borg.cmd(r"who"))
async def _(event):
    rank = None
    if not event.message.is_reply:
        who = await event.get_chat()
    else:
        msg = await event.message.get_reply_message()
        if msg.forward:
            # FIXME forward privacy memes
            who = await borg.get_entity(
                msg.forward.from_id or msg.forward.channel_id)
        else:
            who = await msg.get_sender()
            ic = await event.get_input_chat()
            if isinstance(ic, types.InputPeerChannel):
                rank = getattr((await borg(functions.channels.GetParticipantRequest(
                    ic,
                    who
                ))).participant, 'rank', None)

    await event.edit(get_who_string(who, event.chat_id, rank), parse_mode='html')


@borg.on(borg.cmd(r"members"))
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


@borg.on(borg.cmd(r"active_members"))
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
