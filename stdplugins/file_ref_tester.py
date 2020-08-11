"""
Repeatedly downloads media and posts to @FileRefs
when a FileReferenceExpiredError occurs
"""

import asyncio
import time

from base64 import b64encode, b64decode
from dataclasses import dataclass, field

from telethon import types, utils, errors


@dataclass
class Thing:
    entity_id: int
    message_id: int


@dataclass
class File:
    input_location: [types.InputDocument, types.InputPhoto]
    timestamp: int = field(default_factory=lambda: round(time.time()))
    prev_duration: int = 0


storage.reload({File})

channel_id = 1210997017
things = {}
files = {}
main_loop = None

things['Sticker from pack (channel)'] = Thing(channel_id, 4)
things['Sticker without pack (channel)'] = Thing(channel_id, 7)
things['Photo (channel)'] = Thing(channel_id, 5)
things['Document (channel)'] = Thing(channel_id, 6)
things['GIF (channel)'] = Thing(channel_id, 8)

things['Sticker from pack (pm)'] = Thing(None, 1829)
things['Sticker without pack (pm)'] = Thing(None, 1830)
things['Photo (pm)'] = Thing(None, 1831)
things['Document (pm)'] = Thing(None, 1832)
things['GIF (pm)'] = Thing(None, 1828)

intervals = (
    ('w', 60 * 60 * 24 * 7),
    ('d', 60 * 60 * 24),
    ('h', 60 * 60),
    ('m', 60),
    ('s', 1),
)


def display_time(seconds):
    result = []

    for name, count in intervals:
        value = seconds // count
        if not value:
            continue
        seconds -= value * count
        result.append(f'{value}{name}')
    return ' '.join(result)


async def fetch_file(name):
    thing = things[name]
    m = await borg.get_messages(thing.entity_id, ids=thing.message_id)
    dc_id, input_location = utils.get_input_location(m.media)
    new_file = File(input_location)
    old_file = files.get(name)
    duration_delta = 0
    if old_file:
        new_file.prev_duration = new_file.timestamp - old_file.timestamp
        duration_delta = abs(new_file.prev_duration - old_file.prev_duration)
    files[name] = new_file
    return True, duration_delta >= 300


async def check_file(name, file):
    try:
        async for chunk in borg.iter_download(file.input_location):
            break
        return False, False
    except errors.FileReferenceExpiredError:
        pass

    return await fetch_file(name)


async def send_times_message(changed):
    lines = ['New expiry times (changes marked with *):']
    for name, file in files.items():
        line = f'  {name}: '
        if name in changed:
            line = f'  <b>*{name}</b>: '
        if file.prev_duration:
            line += display_time(file.prev_duration)
        else: 
            line += 'Unknown'
        lines.append(line)

    await borg.send_message(
        channel_id,
        '\n'.join(lines),
        parse_mode='HTML'
    )


async def main():
    storage.files = storage.files or {}
    await borg.get_input_entity('@FileRefs')

    for name in things.keys():
        if name in storage.files:
            files[name] = storage.files[name]
            continue
        await fetch_file(name)
    storage.files = files

    while 1:
        changed = set()
        any_expired = False
        for name, file in files.items():
            has_expired, has_changed = await check_file(name, file)
            any_expired = any_expired or has_expired
            if has_changed:
                changed.add(name)

        if any_expired:
            storage.files = files
        if changed:
            await send_times_message(changed)

        await asyncio.sleep(10 * 60)


def unload():
    if main_loop:
        main_loop.cancel()


main_loop = asyncio.ensure_future(main())