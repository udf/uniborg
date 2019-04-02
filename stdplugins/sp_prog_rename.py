import asyncio
import re

from telethon import events
from telethon.tl.functions.channels import EditTitleRequest
from telethon.errors.rpcerrorlist import ChatNotModifiedError

MULTI_EDIT_TIMEOUT = 10 #80
REVERT_TIMEOUT = 25 #2 * 60 * 60
CHANNEL_ID = 1286178907 #1040270887
DEFAULT_TITLE = "Programming & Tech"
prog_tech_channel = None
rename_lock = asyncio.Lock()


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
        prog_tech_channel = await borg.get_entity(CHANNEL_ID)
    try:
        await borg(EditTitleRequest(
            channel=prog_tech_channel, title=title
        ))
    except ChatNotModifiedError:
        pass  # Everything is ok


async def wait_for_delete(deleted_fut, timeout):
    try:
        await asyncio.wait_for(deleted_fut, timeout)
        await edit_title(DEFAULT_TITLE)
        return True
    except asyncio.TimeoutError:
        pass
    return False


@borg.on(events.NewMessage(
    pattern=re.compile(r"(?i)programming (?:&|and) (.+)"), chats=CHANNEL_ID))
async def on_name(event):
    new_topic = fix_title(event.pattern_match.group(1))
    new_title = f"Programming & {new_topic}"
    if "Tech" not in new_title:
        new_title += " & Tech"

    if len(new_title) > 255 or rename_lock.locked():
        return

    with (await rename_lock):
        await edit_title(new_title)
        deleted_fut = borg.await_event(events.MessageDeleted(
            chats=CHANNEL_ID,
            func=lambda e: e.deleted_id == event.message.id
        ))
        if await wait_for_delete(asyncio.shield(deleted_fut), MULTI_EDIT_TIMEOUT):
            await asyncio.sleep(MULTI_EDIT_TIMEOUT)
            return
    if await wait_for_delete(deleted_fut, REVERT_TIMEOUT) or rename_lock.locked():
        return
    with (await rename_lock):
        await edit_title(DEFAULT_TITLE)
