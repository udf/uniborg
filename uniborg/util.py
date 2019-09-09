# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import functools
import re
import signal

from telethon import events
from telethon.tl.functions.messages import GetPeerDialogsRequest


def admin_cmd(pattern):
    return events.NewMessage(outgoing=True, pattern=re.compile(pattern))


async def is_read(borg, entity, message, is_out=None):
    """
    Returns True if the given message (or id) has been read
    if a id is given, is_out needs to be a bool
    """
    is_out = getattr(message, "out", is_out)
    if not isinstance(is_out, bool):
        raise ValueError(
            "Message was id but is_out not provided or not a bool")
    message_id = getattr(message, "id", message)
    if not isinstance(message_id, int):
        raise ValueError("Failed to extract id from message")

    dialog = (await borg(GetPeerDialogsRequest([entity]))).dialogs[0]
    max_id = dialog.read_outbox_max_id if is_out else dialog.read_inbox_max_id
    return message_id <= max_id


async def get_recent_self_message(borg, event):
    async for message in borg.iter_messages(
            await event.get_input_chat(), limit=20):
        if message.out:
            return message

def _handle_timeout(signum, frame):
    raise TimeoutError("Execution took too long")

def sync_timeout(seconds):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            signal.signal(signal.SIGALRM, _handle_timeout)
            signal.setitimer(signal.ITIMER_REAL, seconds)
            try:
                r = func(*args, **kwargs)
            finally:
                signal.alarm(0)
            return r
        return wrapper
    return decorator
