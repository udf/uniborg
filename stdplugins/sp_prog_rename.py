import asyncio
import re

from telethon import events
from telethon.tl.functions.channels import EditTitleRequest


prog_tech_id = 1040270887
prog_tech_channel = None
default_title = "Programming & Tech"
lock = asyncio.Lock()


def fix_title(s):
    # Ideally this would be a state machine, but ¯\_(ツ)_/¯
    def replace(m):
        token = m.group(1)
        if token.lower() == 'and':
            token = '&'
        return token[0].upper() + token[1:] + (' ' if m.group(2) else '')
    return re.sub(r'(\S+)(\s+)?', replace, s)


async def edit_title(title):
    global prog_tech_channel
    if prog_tech_channel is None:
        prog_tech_channel = await borg.get_entity(prog_tech_id)
    await borg(EditTitleRequest(
        channel=prog_tech_channel, title=title
    ))


@borg.on(events.NewMessage(
    pattern=re.compile(r"(?i)programming (?:&|and) (.+)"), chats=prog_tech_id))
async def on_name(event):
    new_topic = fix_title(event.pattern_match.group(1))
    new_title = f"Programming & {new_topic}"
    if "Tech" not in new_title:
        new_title += " & Tech"

    if len(new_title) > 255 or lock.locked():
        return

    with (await lock):
        await edit_title(new_title)
        await asyncio.sleep(80)
    await asyncio.sleep(2 * 60 * 60)
    if lock.locked():
        return
    with (await lock):
        await edit_title(default_title)
