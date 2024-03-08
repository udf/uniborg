from telethon import events


@borg.on(events.NewMessage(chats=[1256902287], from_users=[1006503122]))
async def comment(event):
  await event.reply('first?')
