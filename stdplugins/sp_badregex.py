import asyncio
from telethon import events

import re


@borg.on(events.NewMessage(
    pattern=re.compile(r"^s/((?:\\/|[^/])+)/((?:\\/|[^/])*)(/.*)?")))
async def on_regex(re_event):
    re_msg = re_event.message

    async def filter_botanswer(bot_event):
        bot_msg = bot_event.message
        if bot_msg.reply_to_msg_id == re_msg.id:
            return False
        if re_msg.reply_to_msg_id and bot_msg.reply_to_msg_id:
            if bot_msg.reply_to_msg_id != re_msg.reply_to_msg_id:
                return False
        if bot_msg.message and '[[regex]]' in bot_msg.message:
            return True
        if not (await bot_event.sender).bot:
            return False
        return True

    if re_event.is_private:
        return

    try:
        await asyncio.wait_for(
            borg.await_event(
                events.NewMessage(chats=await re_event.input_chat),
                filter_botanswer
            ),
            timeout=3
        )
    except asyncio.TimeoutError:
        await re_event.reply("nice regex bro")
