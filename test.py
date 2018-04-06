from uniborg import Uniborg
from telethon import events

borg = Uniborg("uniborg")

print(borg.uid)
print(dir(borg))

@borg.on(events.NewMessage)
async def asdf(e):
    print(e.raw_text)

borg.run()
