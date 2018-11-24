import asyncio

from telethon.errors import MessageEmptyError
from telethon.tl.functions.messages import SaveDraftRequest
from telethon.tl.functions.messages import EditMessageRequest

from stdplugins.kbass_core import self_reply_cmd


@self_reply_cmd(borg, r"^\.e$")
async def on_edit_start(event, target):
    await asyncio.sleep(3)  # tdesktop doesn't sync drafts when the window is active
    await borg(SaveDraftRequest(
        peer=await event.get_input_chat(),
        message=(target.message or '.') + '\n.e',
        entities=target.entities,
        no_webpage=not target.media,
        reply_to_msg_id=target.id
    ))


@self_reply_cmd(borg, r'(?ms)^(.+)\.e$')
async def on_edit_end(event, target):
    text = event.pattern_match.group(1)
    message = event.message.message[:-2]
    if message.strip() == '.':
        message = ''
    try:
        await borg(EditMessageRequest(
            peer=await event.get_input_chat(),
            id=target.id,
            no_webpage=not target.media,
            message=message,
            entities=event.message.entities
        ))
    except MessageEmptyError:
        # Can't make text message empty, so delete it
        await borg.delete_messages(chat, target)
