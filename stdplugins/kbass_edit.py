"""
Reply to a message with .e to make a draft of it (with '\n.e' appended)
Reply to your own message with <text>.e to edit the message to <text>
if <text> is ".", the message is edited to empty/deleted
"""
import asyncio

from telethon.errors import MessageEmptyError
from telethon.tl.functions.messages import SaveDraftRequest
from telethon.tl.functions.messages import EditMessageRequest

from stdplugins.kbass_core import self_reply_cmd


@self_reply_cmd(borg, r"^\.e$")
async def on_edit_start(event, target):
    await borg(SaveDraftRequest(
        peer=await event.get_input_chat(),
        message=(target.message or '.') + '\n.e',
        entities=target.entities,
        no_webpage=not target.media,
        reply_to_msg_id=target.id
    ))


@self_reply_cmd(borg, r'(?ms)^(.+\n|\.)\.e$')
async def on_edit_end(event, target):
    text = event.pattern_match.group(1)
    if text == '.':
        text = ''
    chat = await event.get_input_chat()
    try:
        await borg(EditMessageRequest(
            peer=chat,
            id=target.id,
            no_webpage=not target.media,
            message=text,
            entities=event.message.entities
        ))
    except MessageEmptyError:
        # Can't make text message empty, so delete it
        await borg.delete_messages(chat, target)
