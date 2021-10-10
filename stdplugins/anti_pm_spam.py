import asyncio
from datetime import datetime

from telethon import events
from telethon.tl.types import InputPeerNotifySettings
from telethon.tl.functions.account import UpdateNotifySettingsRequest
from telethon.tl.functions.messages import ReadHistoryRequest, ReportSpamRequest
from telethon.tl.functions.contacts import BlockRequest

pending_uids = set()
verify_msg = 'I am a human, this action was performed manually'


@borg.on(events.NewMessage(
  incoming=True,
  func=lambda e: e.is_private and e.sender_id in pending_uids and e.raw_text == verify_msg
))
async def on_verify(event):
  logger.info(f'{event.sender_id} has been verified')
  pending_uids.discard(event.sender_id)
  await event.respond('You have verified yourself as a human.')

  await borg(UpdateNotifySettingsRequest(
    await event.get_input_chat(),
    InputPeerNotifySettings()
  ))


async def wait_for_verify(uid, chat):
  await asyncio.sleep(60 * 5)
  if uid not in pending_uids:
    return
  pending_uids.discard(uid)

  logger.info(f'{uid} failed to verify')
  await borg.send_message(
    chat,
    'You failed to perform the verification in time, goodbye.'
  )
  
  await borg(BlockRequest(chat))
  await borg(ReportSpamRequest(chat))


@borg.on(events.NewMessage(incoming=True))
async def on_msg(event):
  if not event.is_private:
    return

  uid = event.sender_id
  seen_users = storage.seen or set()
  if uid in seen_users:
    return
  seen_users.add(uid)
  storage.seen = seen_users

  sender = await event.get_sender()
  if sender.contact or sender.bot:
    return

  chat = await event.get_input_chat()

  logger.info(f'asking {uid} to verify')

  await borg(ReadHistoryRequest(chat, 0))
  await borg.forward_messages(
    chat,
    [941215],
    'me'
  )

  await borg(UpdateNotifySettingsRequest(
    chat,
    InputPeerNotifySettings(
      show_previews=False,
      mute_until=datetime.utcfromtimestamp(2**31 - 1)
    )
  ))

  pending_uids.add(uid)
  asyncio.create_task(wait_for_verify(uid, chat))