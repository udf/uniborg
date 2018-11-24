"""
Reply to a message with .s <n> to forward <n> messages from that point to your
saved messages (negative values of <n> go backwards in history)
"""
import asyncio

from stdplugins.kbass_core import self_reply_selector


@self_reply_selector(borg, r'\.s')
async def on_save(event, targets, num_offset):
    await borg.forward_messages('me', targets)
    msg = await event.respond(f'Saved {abs(num_offset) + 1} messages!')
    await asyncio.sleep(3)
    await borg.delete_messages(msg.to_id, msg)
