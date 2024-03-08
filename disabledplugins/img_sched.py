import asyncio
import os
import traceback
from pathlib import Path
import time
from datetime import datetime, timezone, timedelta


def walk_files(path):
  for root, dirs, files in os.walk(path):
    root = Path(root)
    for file in files:
      yield root / file


tz = timezone(timedelta(hours=2))
files = []

for f in walk_files('img_sched'):
  d = datetime.strptime(f.stem, "%Y-%m-%d %H:%M:%S")
  d = d.replace(tzinfo=tz)
  files.append((f, d))

files = sorted(files, key=lambda x: x[1])


async def do_thing(f, date):
  delta = datetime.now(tz) - date
  if delta > timedelta(0):
    logger.info(f'skipping {f}')
    return

  logger.info(f'sending {f}')
  delta = date - datetime.now(tz)
  while delta > timedelta(minutes=2):
    logger.info(f'(long sleep) delta is {delta}')
    await asyncio.sleep(30)
    delta = date - datetime.now(tz)

  delta = datetime.now(tz) - date
  logger.info(f'uploading file...')
  s = time.time()
  uploaded_file = await borg.upload_file(f)
  logger.info(f'file uploaded in {round((time.time() - s) * 1000)}ms')

  logger.info(f'short sleeping...')
  while datetime.now(tz) < date:
    await asyncio.sleep(0.01)

  logger.info(f'sending file...')
  await borg.send_message(
    '@ZXY101',
    file=uploaded_file
  )



async def main():
  for f, d in files:
    try:
      await do_thing(f, d)
    except Exception as e:
      logger.error(f'Error sending {f}: {e}')
      logger.error(traceback.format_exc())
  logger.info('out of files')



def unload():
  if main_loop:
    main_loop.cancel()


main_loop = asyncio.ensure_future(main())