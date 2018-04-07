from telethon import events

@borg.on(events.NewMessage)
async def asdf(e):
    print(e.raw_text)
