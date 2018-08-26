from telethon import events
from telethon.tl import types

@borg.on(events.NewMessage(pattern=r"^h$", outgoing=False))
async def on_h(event):
    await borg.send_message(await event.get_input_chat(), '',
        file=types.InputDocument(421851232546587302, -6059663575626880183),
        reply_to=event.message.id)
