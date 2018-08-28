# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from telethon import events
from telethon import utils
from telethon.tl import types


@borg.on(events.NewMessage(pattern=r"\.who", outgoing=True))
async def _(event):
    if not event.message.is_reply:
        who = await event.get_chat()
    else:
        msg = await event.message.get_reply_message()
        if msg.forward:
            who = await borg.get_entity(
                msg.forward.from_id or msg.forward.channel_id)
        else:
            who = await msg.get_sender()

    who_string = utils.get_display_name(who)
    if isinstance(who, (types.User, types.Channel)) and who.username:
        who_string += f" (@{who.username})"
    who_string += f", #{who.id}"

    await event.edit(who_string)
