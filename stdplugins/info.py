# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from telethon import events
from telethon.utils import add_surrogate
from telethon.tl.types import MessageEntityPre
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
            result.append(f'{k}: {formatted}')
            result.append('\n')
        result.pop()
        indent -= 2
        result.append(' ' * indent)
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
        result.append(' ' * indent)
    else:
        return repr(obj)

    return ''.join(result)


@borg.on(events.NewMessage(pattern=r"\.info", outgoing=True))
async def _(event):
    if not event.message.is_reply:
        return
    msg = await event.message.get_reply_message()
    yaml_text = yaml_format(msg)
    await event.edit(yaml_text, parse_mode=parse_pre)
