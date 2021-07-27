# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""
Show all .info about the replied message
"""
from telethon import events
from telethon.utils import add_surrogate
from telethon.tl.functions.channels import GetParticipantRequest
from telethon.tl.types import InputPeerChannel, MessageEntityPre
from telethon.tl.tlobject import TLObject
import datetime

STR_LEN_MAX = 256
BYTE_LEN_MAX = 64


def parse_pre(text):
    text = text.strip()
    return (
        text,
        [MessageEntityPre(offset=0, length=len(add_surrogate(text)), language='')]
    )


def yaml_format(obj, indent=0):
    """
    Pretty formats the given object as a YAML string which is returned.
    (based on TLObject.pretty_format)
    """
    result = []
    if isinstance(obj, TLObject):
        obj = obj.to_dict()

    if isinstance(obj, dict):
        if not obj:
            return 'dict:'
        result.append(obj.get('_', 'dict') + ':')
        items = obj.items()
        has_multiple_items = len(items) > 2
        if has_multiple_items:
            result.append('\n')
            indent += 2
        for k, v in items:
            if k == '_' or v is None:
                continue
            formatted = yaml_format(v, indent)
            if not formatted.strip():
                continue
            result.append(' ' * (indent if has_multiple_items else 1))
            result.append(f'{k}:')
            if not formatted[0].isspace():
                result.append(' ')
            result.append(f'{formatted}')
            result.append('\n')
        result.pop()
        if has_multiple_items:
            indent -= 2
    elif isinstance(obj, str):
        # truncate long strings and display elipsis
        result = repr(obj[:STR_LEN_MAX])
        if len(obj) > STR_LEN_MAX:
            result += '…'
        return result
    elif isinstance(obj, bytes):
        # repr() bytes if it's printable, hex like "FF EE BB" otherwise
        if all(0x20 <= c < 0x7f for c in obj):
            return repr(obj)
        else:
            return ('<…>' if len(obj) > BYTE_LEN_MAX else
                    ' '.join(f'{b:02X}' for b in obj))
    elif isinstance(obj, datetime.datetime):
        # ISO-8601 without timezone offset (telethon dates are always UTC)
        return obj.strftime('%Y-%m-%d %H:%M:%S')
    elif hasattr(obj, '__iter__'):
        # display iterables one after another at the base indentation level
        result.append('\n')
        indent += 2
        for x in obj:
            result.append(f"{' ' * indent}- {yaml_format(x, indent + 2)}")
            result.append('\n')
        result.pop()
        indent -= 2
    else:
        return repr(obj)

    return ''.join(result)


@borg.on(borg.cmd("info"))
async def _(event):
    if not event.message.is_reply:
        await who(event)
        return
    msg = await event.message.get_reply_message()
    yaml_text = yaml_format(msg)
    action = event.edit if not borg.me.bot else event.respond
    await action(yaml_text, parse_mode=parse_pre)


@borg.on(borg.cmd("who"))
async def who(event):
    participant = None
    if not event.message.is_reply:
        who = await event.get_chat()
    else:
        msg = await event.message.get_reply_message()
        if msg.forward:
            if msg.forward.from_name is not None:
                who = msg.forward.original_fwd
            else:
                who = await borg.get_entity(
                    msg.forward.sender_id or msg.forward.chat_id)
        else:
            who = await msg.get_sender()
            ic = await event.get_input_chat()
            if isinstance(ic, InputPeerChannel):
                participant = (await borg(GetParticipantRequest(
                    ic,
                    who
                ))).participant
    yaml_text = yaml_format(who)
    if participant is not None:
        yaml_text += "\n"
        yaml_text += yaml_format(participant)
    action = event.edit if not borg.me.bot else event.respond
    await action(yaml_text, parse_mode=parse_pre)