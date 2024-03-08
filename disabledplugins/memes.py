import asyncio

import random

from telethon.tl import types
from telethon import events
import telethon.tl.functions as tlf

actions = [
  types.SendMessageGamePlayAction(),
  types.SendMessageRecordRoundAction(),
  types.SendMessageTypingAction(),
  types.SendMessageUploadDocumentAction(1),
  types.SendMessageUploadRoundAction(1),
  types.SendMessageRecordAudioAction(),
  types.SendMessageRecordVideoAction(),
  types.SendMessageUploadAudioAction(1),
  types.SendMessageUploadPhotoAction(1),
  types.SendMessageUploadVideoAction(1)
]

@borg.on(events.NewMessage(chats='@ZXY101'))
async def read(event):
  print(f'marking as read')
  await borg(tlf.messages.ReadHistoryRequest('@ZXY101', event.id))


async def memes():
  while 1:
    action = random.choice(actions)
    print(f'sending {action}')
    await borg(tlf.messages.SetTypingRequest('@ZXY101', action))
    await asyncio.sleep(random.randint(10, 20))

asyncio.ensure_future(memes())
