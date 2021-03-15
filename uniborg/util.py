# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import re
import signal
import inspect
import functools
from time import time
from PIL import Image
from io import BytesIO
import asyncio
import concurrent.futures
from random import randrange
from collections import defaultdict


from telethon import events
from telethon.tl.functions.messages import GetPeerDialogsRequest


# Cooldown in seconds
def cooldown(timeout):
    def wrapper(function):
        last_called = defaultdict(int)

        async def wrapped(event, *args, **kwargs):
            current_time = time()
            if current_time - last_called[event.chat_id] < timeout:
                time_left = round(timeout - (current_time - last_called[event.chat_id]), 1)
                return
            last_called[event.chat_id] = current_time
            return await function(event, *args, **kwargs)
        wrapped.__module__ = function.__module__
        return wrapped
    return wrapper


# 1 in amount chance of running the function
def chance(amount, lower=1):
    def wrapper(function):
        async def wrapped(event, *args, **kwargs):
            res = randrange(amount)
            if res != 0:
                return
            await function(event, *args, **kwargs)
        wrapped.__module__ = function.__module__
        return wrapped
    return wrapper


# Downscale an image so it doesn't look bad
executor = concurrent.futures.ThreadPoolExecutor()
async def downscale(fp, max_w=1280, max_h=1280, format="PNG"):
    def wrapped(fp, max_w=1280, max_h=1280, format="PNG"):
        im = Image.open(fp)
        res = im.size
        out_im = BytesIO()

        im.thumbnail((max_w, max_h), Image.LANCZOS)
        im.save(out_im, format)
        out_im.seek(0)

        return out_im, res

    return await asyncio.get_event_loop().run_in_executor(
        executor,
        lambda: wrapped(fp, max_w, max_w, format)
    )


async def blacklist(event, blacklist=None):
    if blacklist is None:
        blacklist = set()

    m = event.pattern_match
    shortname = m["shortname"]
    remove = m.group(1)
    file_name = inspect.currentframe().f_back.f_code.co_filename

    if shortname not in file_name:
        return

    group = event.chat_id
    if not remove:
        blacklist.add(group)
    else:
        blacklist.discard(group)

    msg = await event.respond("Updated blacklist.")
    await asyncio.sleep(5)
    await msg.delete()

    return blacklist


def edit_blacklist(group, blacklist=None, remove=False):
    if blacklist is None:
        blacklist = set()

    if not remove:
        blacklist.add(group)
    else:
        blacklist.discard(group)

    return blacklist


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


async def get_target_self_message(borg, event):
    """
    Returns the reply message if it's from us.
    Otherwise returns the most recent message from us
    """
    target = await event.get_reply_message()
    if event.is_reply and target.out:
        return target
    if not target:
        return await get_recent_self_message(borg, event)


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

async def send_replacement_message(event, *args, **kwargs):
    """
    Same as event.respond()
    but with reply_to already set to what this event is replying to
    """
    if 'reply_to' in kwargs:
        raise ValueError("reply_to must not be provided")
    kwargs['reply_to'] = event.message.reply_to_msg_id
    return await event.respond(*args, **kwargs)
