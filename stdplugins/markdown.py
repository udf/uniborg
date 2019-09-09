# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import re
from functools import partial

from telethon import events
from telethon.tl.functions.messages import EditMessageRequest
from telethon.extensions.markdown import DEFAULT_URL_RE
from telethon.utils import add_surrogate, del_surrogate
from telethon.tl.types import MessageEntityTextUrl


def parse_url_match(m):
    entity = MessageEntityTextUrl(
        offset=m.start(),
        length=len(m.group(1)),
        url=del_surrogate(m.group(2))
    )
    return m.group(1), entity


def parse_aesthetics(m):
    def aesthetify(string):
        for c in string:
            if " " < c <= "~":
                yield chr(ord(c) + 0xFF00 - 0x20)
            elif c == " ":
                yield "\u3000"
            else:
                yield c
    return "".join(aesthetify(m[1])), None


def parse_strikethrough(m):
    return ("\u0336".join(m[1]) + "\u0336"), None


def parse_enclosing_circle(m):
    return ("\u20e0".join(m[1]) + "\u20e0"), None


def parse_subreddit(m):
    text = '/' + m.group(3)
    entity = MessageEntityTextUrl(
        offset=m.start(2),
        length=len(text),
        url=f'reddit.com{text}'
    )
    return m.group(1) + text, entity


def parse_snip(m):
    try:
        name = m.group(1)[1:]
        snip = borg._plugins['snip'].storage.snips[name]
        if snip['type'] == borg._plugins['snip'].TYPE_TEXT:
            return snip['text'], None
    except KeyError:
        pass
    return m.group(1), None


# A matcher is a tuple of (regex pattern, parse function)
# where the parse function takes the match and returns (text, entity)
MATCHERS = [
    (DEFAULT_URL_RE, parse_url_match),
    (re.compile(r'!\+(.+?)\+!'), parse_aesthetics),
    (re.compile(r'~~(.+?)~~'), parse_strikethrough),
    (re.compile(r'@@(.+?)@@'), parse_enclosing_circle),
    (re.compile(r'([^/\w]|^)(/?(r/\w+))'), parse_subreddit),
    (re.compile(r'(!\w+)'), parse_snip)
]


def parse(message, old_entities=None):
    entities = []
    old_entities = sorted(old_entities or [], key=lambda e: e.offset)

    i = 0
    after = 0
    message = add_surrogate(message)
    while i < len(message):
        for after, e in enumerate(old_entities[after:], start=after):
            # If the next entity is strictly to our right, we're done here
            if i < e.offset:
                break
            # Skip already existing entities if we're at one
            if i == e.offset:
                i += e.length
        else:
            after += 1

        # Find the first pattern that matches
        for pattern, parser in MATCHERS:
            match = pattern.match(message, pos=i)
            if match:
                break
        else:
            i += 1
            continue

        text, entity = parser(match)

        # Shift old entities after our current position (so they stay in place)
        shift = len(text) - len(match[0])
        if shift:
            for e in old_entities[after:]:
                e.offset += shift

        # Replace whole match with text from parser
        message = ''.join((
            message[:match.start()],
            text,
            message[match.end():]
        ))

        # Append entity if we got one
        if entity:
            entities.append(entity)

        # Skip past the match
        i += len(text)

    return del_surrogate(message), entities + old_entities


@borg.on(events.MessageEdited(outgoing=True))
@borg.on(events.NewMessage(outgoing=True))
async def reparse(event):
    old_entities = event.message.entities or []
    parser = partial(parse, old_entities=old_entities)
    message, msg_entities = await borg._parse_message_text(event.raw_text, parser)
    if len(old_entities) >= len(msg_entities) and event.raw_text == message:
        return

    await borg(EditMessageRequest(
        peer=await event.get_input_chat(),
        id=event.message.id,
        message=message,
        no_webpage=not bool(event.message.media),
        entities=msg_entities
    ))
    raise events.StopPropagation
