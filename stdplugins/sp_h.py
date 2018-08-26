from telethon import events
from telethon.tl import types

@borg.on(events.NewMessage(pattern="^h$", outgoing=False))
async def on_h(event):
    await borg.reply(file="CAADAQADpgIAAna32gVJ62JcFcDnqwI")
