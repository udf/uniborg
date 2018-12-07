"""
Like save but makes a draft in your chat of all the messages concatenated with
two newlines
"""
import html

from telethon.tl.functions.messages import SaveDraftRequest
from telethon.extensions import html as thtml

from stdplugins.kbass_core import self_reply_selector


def get_message_html(message):
    if message.action:
        return html.escape(str(message.action))
    return thtml.unparse(message.message, message.entities)


@self_reply_selector(borg, r'\.y')
async def on_yank(event, targets, num_offset):
    message = '\n\n'.join(get_message_html(target) for target in targets)
    message, entities = thtml.parse(message)
    await borg(SaveDraftRequest(
        peer=await event.get_input_chat(),
        message=message,
        entities=entities,
        no_webpage=True,
    ))
