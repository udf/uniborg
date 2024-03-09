import asyncio

from telethon import functions, types

emoji_documents = {
  'pink' : 6003623690007220779,
  'white' : 6005930113214976252,
  'blue' : 6005560329415697013
}
document_order = [
  emoji_documents['blue'],
  emoji_documents['pink'],
  emoji_documents['white'],
  emoji_documents['pink'],
]


async def main():
  previous_doc = None
  while 1:
    for document_id in document_order:
      if document_id != previous_doc:
        await borg(functions.account.UpdateEmojiStatusRequest(
          emoji_status=types.EmojiStatus(document_id=document_id)
        ))
      previous_doc = document_id
      await asyncio.sleep(30)


def unload():
  if main_loop:
    main_loop.cancel()


main_loop = asyncio.ensure_future(main())