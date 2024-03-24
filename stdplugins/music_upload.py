import asyncio
from pathlib import Path
import json
from io import BytesIO
import shutil

import mutagen
from PIL import Image
from telethon import utils


def get_embedded_art(f):
  m = mutagen.File(f)
  pics = []
  if isinstance(m, mutagen.flac.FLAC):
    pics = [p.data for p in m.pictures]
  elif isinstance(m, mutagen.mp3.MP3):
    pics = [m.get(k).data for k in m.keys() if k.startswith('APIC:')]
  else:
    raise NotImplementedError
  return pics


def get_music_thumb(f):
  im = None
  if arts := get_embedded_art(f):
    im = Image.open(BytesIO(arts[0]))

  if not im:
    return

  im = im.convert('RGB')
  im.thumbnail((320, 320))
  data = BytesIO()
  im.save(data, format='jpeg')
  data.seek(0)
  return data


def next_uploadable_dir():
  src_dir = Path('/sync/music_tg')
  for metafile in sorted(src_dir.glob('*/meta.json')):
    with open(metafile) as f:
      metadata = json.load(f)

    if metadata.get('skip'):
      continue

    parent = metafile.parent
    if all((parent / path).exists() for path in metadata['files']):
      yield parent, metadata
      break


def get_music_attributes(path):
  concat = lambda l: ', '.join(l) or None
  attrs = [DocumentAttributeFilename(path.name)]
  m = mutagen.File(path)

  title = None
  performer = None
  if isinstance(m, mutagen.flac.FLAC):
    title = concat(m.tags.get('TITLE', []))
    performer = concat(m.tags.get('ARTIST', []))
  elif isinstance(m, mutagen.mp3.MP3):
    title = concat(m.tags.get('TIT2', []))
    performer = concat(m.tags.get('TPE1', []))

  attrs.append(DocumentAttributeAudio(
    duration=int(m.info.length) if m.info.length else 0,
    title=title,
    performer=performer,
    voice=False
  ))

  return attrs


async def upload_dir(path, metadata):
  num_files = len(metadata["files"])
  logger.info(f'Uploading {str(path)!r} ({num_files} files)...')
  entity = await borg.get_entity(metadata.get('dest', '@musicwastaken'))

  attributes = [get_music_attributes(path / filename) for filename in metadata['files']]
  thumbs = [get_music_thumb(path / filename) for filename in metadata['files']]

  uploaded_files = []
  for filename in metadata['files']:
    handle = await borg.upload_file(path / filename, part_size_kb=512)
    uploaded_files.append(handle)

  messages = []
  for filename, handle, attrs, thumb in zip(metadata['files'], uploaded_files, attributes, thumbs):
    message = await borg.send_file(
      entity,
      file=handle,
      thumb=thumb,
      attributes=attrs
    )
    messages.append(message)

  pins = set(metadata['pins'])
  for filename, message in zip(metadata['files'], messages):
    if filename in pins:
      await borg.pin_message(entity, message)

  shutil.rmtree(path)
  return num_files


async def main():
  while 1:
    for path, metadata in next_uploadable_dir():
      try:
        num_uploaded = await upload_dir(path, metadata)
        await asyncio.sleep(180 * num_uploaded)
        break
      except Exception as e:
        # <1> sets the systemd log level, will get sent to tg via watcher bot
        print(f'<1>Unhandled exception uploading {str(path)!r}')
        logger.exception('Unhandled exception in upload loop')
        await asyncio.sleep(300)
    else:
      await asyncio.sleep(60)


def unload():
  if main_loop:
    main_loop.cancel()


main_loop = asyncio.ensure_future(main())