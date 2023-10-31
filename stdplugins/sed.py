"""
Become @regexbot when the bot is missing
"""

import regex as re
from collections import defaultdict, deque

from telethon import events, utils
from telethon.tl import types, functions

from uniborg import util

SED_PATTERN = r'^s/((?:\\/|[^/])+)/((?:\\/|[^/])*)(/.*)?'
GROUP0_RE = re.compile(r'(?<!\\)((?:\\\\)*)\\0')
HEADER = '' if borg.me.bot else '「sed」\n'
KNOWN_RE_BOTS = re.compile(
    r'(regex|moku|ou|BananaButler_|rgx|l4mR|ProgrammingAndGirls)bot',
    flags=re.IGNORECASE
)

# Heavily based on
# https://github.com/SijmenSchoon/regexbot/blob/master/regexbot.py

last_msgs = defaultdict(lambda: deque(maxlen=10))


def cleanup_pattern(match):
    from_ = match.group(1)
    to = match.group(2)

    to = to.replace('\\/', '/')
    to = GROUP0_RE.sub(r'\1\\g<0>', to)

    return from_, to


#@util.sync_timeout(1)
async def doit(command, match):
    fr, to = cleanup_pattern(match)

    try:
        fl = match.group(3)
        if fl is None:
            fl = ''
        fl = fl[1:]
    except IndexError:
        fl = ''

    # Build Python regex flags
    count = 1
    flags = 0
    for f in fl.lower():
        if f == 'i':
            flags |= re.IGNORECASE
        elif f == 'm':
            flags |= re.MULTILINE
        elif f == 's':
            flags |= re.DOTALL
        elif f == 'g':
            count = 0
        elif f == 'x':
            flags |= re.VERBOSE
        else:
            await command.reply(f'{HEADER}Unknown flag: {f}')
            return

    def substitute(s):
        if not s:
            return None

        if s.startswith(HEADER):
            s = s[len(HEADER):]

        s, i = re.subn(fr, to, s, count=count, flags=flags)
        if i > 0:
            return s

    try:
        if command.is_reply:
            if command.reply_to.reply_from is not None:
                # External reply
                reply_to = command.id
            else:
                reply_to = command.reply_to.reply_to_msg_id

            original_text = (
                command.reply_to.quote_text
                or (await command.get_reply_message()).raw_text
            )

            substitution = substitute(original_text)
        else:
            for msg in reversed(last_msgs[command.chat_id]):
                reply_to = msg.id
                substitution = substitute(msg.raw_text)
                if substitution is not None:
                    break  # msg is also set

        if substitution is not None:
            return await command.respond(
                f'{HEADER}{substitution}',
                parse_mode=None,
                reply_to=reply_to,
            )

    except Exception as e:
        await command.reply(f'{HEADER}fuck me: {e}')


async def group_has_sedbot(group):
    if isinstance(group, types.InputPeerChannel):
        full = await borg(functions.channels.GetFullChannelRequest(group))
    elif isinstance(group, types.InputPeerChat):
        full = await borg(functions.messages.GetFullChatRequest(group.chat_id))
    else:
        return False

    return any(KNOWN_RE_BOTS.match(x.username or '') for x in full.users)

async def sed(event):
    if event.fwd_from:
        return
    if not (borg.me.bot or event.is_private):
        if not event.out:
            return
        if await group_has_sedbot(await event.get_input_chat()):
            return

    message = await doit(event.message, event.pattern_match)
    if message:
        last_msgs[event.chat_id].append(message)

    # Don't save sed commands or we would be able to sed those
    raise events.StopPropagation


@borg.on(events.NewMessage)
async def catch_all(event):
    last_msgs[event.chat_id].append(event.message)


@borg.on(events.MessageEdited)
async def catch_edit(event):
    for i, message in enumerate(last_msgs[event.chat_id]):
        if message.id == event.id:
            last_msgs[event.chat_id][i] = event.message


borg.on(events.NewMessage(pattern=SED_PATTERN))(sed)
borg.on(events.MessageEdited(pattern=SED_PATTERN))(sed)
