"""
Repeatedly downloads media and posts to @FileRefs
when a FileReferenceExpiredError occurs
"""

import asyncio
import time
import pickle

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

# Fix pickle not being able to import classes from this module
from stdplugins.file_ref_tester import File

channel_id = 1210997017
things = {}
files = {}
main_loop = None

if '_UniborgPlugins' in __name__ :
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
    ('weeks', 60 * 60 * 24 * 7),
    ('days', 60 * 60 * 24),
    ('hours', 60 * 60),
    ('minutes', 60),
    ('seconds', 1),
)


def display_time(seconds):
    result = []

    for name, count in intervals:
        value = seconds // count
        if not value:
            continue
        seconds -= value * count
        if value == 1:
            name = name.rstrip('s')
        result.append("{} {}".format(value, name))
    return ', '.join(result)


def store_files():
    out = {}
    for name, file in files.items():
        out[name] = b64encode(pickle.dumps(file)).decode('ascii')
    storage.files = out


async def fetch_file(name):
    thing = things[name]
    m = await borg.get_messages(thing.entity_id, ids=thing.message_id)
    dc_id, input_location = utils.get_input_location(m.media)
    new_file = File(input_location)
    old_file = files.get(name)
    prev_duration = new_file.prev_duration
    if old_file:
        new_file.prev_duration = new_file.timestamp - old_file.timestamp
    files[name] = new_file
    return new_file, abs(prev_duration - new_file.prev_duration)


async def check_file(name, file):
    try:
        async for chunk in borg.iter_download(file.input_location):
            break
        return None, 0
    except errors.FileReferenceExpiredError:
        pass

    return await fetch_file(name)


async def send_times_message(duration_deltas):
    lines = ['New expiry times (changes marked with *):']
    for name, file in files.items():
        line = f'  {name}: '
        if duration_deltas.get(name, 0) >= 300:
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
            files[name] = pickle.loads(b64decode(storage.files[name]))
            continue
        await fetch_file(name)
    store_files()

    while 1:
        new_duration_deltas = {}
        for name, file in files.items():
            new_file, duration_delta = await check_file(name, file)
            if new_file:
                new_duration_deltas[name] = duration_delta

        if new_duration_deltas:
            store_files()
            await send_times_message(new_duration_deltas)

        await asyncio.sleep(10 * 60)


def unload():
    if main_loop:
        main_loop.cancel()


if '_UniborgPlugins' in __name__ :
    main_loop = asyncio.ensure_future(main())