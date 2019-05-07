"""
Reply to a message with .d <n> to delete <n> messages from that point
(negative values of <n> go backwards in history)
"""
import asyncio

from stdplugins.kbass_core import self_reply_selector


@self_reply_selector(borg, r'\.d')
async def on_save(event, targets, num_offset):
    await borg.delete_messages(
        await event.get_input_chat(),
        targets
    )