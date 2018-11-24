"""
Reply to a message with .p <y/n> to toggle the webpage preview of a message
"""
from telethon.errors import MessageNotModifiedError
from telethon.tl.functions.messages import EditMessageRequest

from stdplugins.kbass_core import self_reply_cmd


@self_reply_cmd(borg, r"^\.p(?: ?)([yn])?$")
async def on_edit_preview(event, target):
    preview = event.pattern_match.group(1) == 'y'
    if not event.pattern_match.group(1):
        preview = not bool(target.media)
    try:
        await borg(EditMessageRequest(
            peer=await event.get_input_chat(),
            id=target.id,
            no_webpage=not preview,
            message=target.message,
            entities=target.entities
        ))
    except MessageNotModifiedError:
        # There was no preview to modify
        pass
