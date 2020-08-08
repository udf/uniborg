"""
Toggles the webpage preview of a replied to/most recent message
"""

from uniborg import util

from telethon.errors import MessageNotModifiedError
from telethon.tl.functions.messages import EditMessageRequest


@borg.on(borg.admin_cmd('p'))
async def on_edit_preview(event):
    await event.delete()
    target = await util.get_target_self_message(borg, event)
    if not target:
        return
    try:
        await borg(EditMessageRequest(
            peer=await event.get_input_chat(),
            id=target.id,
            no_webpage=bool(target.media),
            message=target.message,
            entities=target.entities
        ))
    except MessageNotModifiedError:
        # There was no preview to modify
        pass
