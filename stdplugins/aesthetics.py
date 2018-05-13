# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from telethon import events
from telethon.tl.functions.messages import EditMessageRequest

PRINTABLE_ASCII = range(0x20, 0x7f)


def aesthetify(string):
    for c in string:
        c = ord(c)
        if c in PRINTABLE_ASCII:
            c += 0xFF00 - 0x20
        yield chr(c)


@borg.on(events.NewMessage(pattern=r'.ae (\S+)', outgoing=True))
async def _(event):
    text = event.pattern_match.group(1)
    text = "".join(aesthetify(text))

    await borg(EditMessageRequest(
        peer=await event.input_chat,
        id=event.message.id,
        message=text,
        no_webpage=not bool(event.message.media)
    ))
