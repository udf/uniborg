"""
  Runs ffprobe on a media file without downloading the whole thing
"""
import asyncio
from asyncio import subprocess
from dataclasses import dataclass
import math
from pathlib import Path
import time
from secrets import token_hex

from uniborg.util import parse_pre

import telethon
from telethon.tl.types import DocumentAttributeFilename
from telethon.errors.rpcerrorlist import MessageTooLongError
from telethon.tl import types

import ffmpeg
from aiohttp import web, hdrs


CHUNK_SIZE = 512 * 1024
# https://i.redd.it/snr1q4nimaa71.jpg
FFPROBE_PATH = Path(ffmpeg.input('').output('').compile()[0]).with_name('ffprobe')

HTTP_PORT = None
unload = None


@dataclass
class FileJob:
  file: types.TypeMessageMedia
  size: int
  bytes_downloaded: int = 0

file_jobs: dict[str, FileJob] = {}


async def http_handler(request):
  job = file_jobs.get(request.match_info.get('id'), None)
  if not job:
    raise web.HTTPNotFound()

  response = web.StreamResponse(status=206)
  response.content_type = 'application/octet-stream'

  range_start = request.http_range.start or 0
  range_end = request.http_range.stop or job.size
  bytes_to_read = range_end - range_start + 1
  response.content_length = bytes_to_read
  response.headers[hdrs.CONTENT_RANGE] = f'bytes {range_start}-{range_end}/{job.size}'

  await response.prepare(request)

  bytes_read = 0
  try:
    async for chunk in borg.iter_download(
      job.file,
      offset=range_start,
      limit=math.ceil(bytes_to_read / CHUNK_SIZE)
    ):
      bytes_read += len(chunk)
      if len(chunk) > bytes_to_read:
        chunk = chunk[:bytes_to_read]
      await response.write(chunk)
      bytes_to_read -= len(chunk)
  finally:
    job.bytes_downloaded += bytes_read

  return response


@borg.on(borg.admin_cmd(r'(ff)?probe'))
async def on_ffprobe(event):
  await event.delete()
  target = await event.get_reply_message()
  if not target or not target.media:
    return
  # skip non-downloadable media
  try:
    telethon.utils._get_file_info(target.media)
  except TypeError:
    return

  job_id = f'{event.chat_id}_{event.message.id}_{token_hex(4)}'
  file_name = target.file.name
  if not file_name:
    file_name = 'media' + (target.file.ext or '')
  file_jobs[job_id] = FileJob(target.media, target.file.size)

  start_time = time.time()
  proc = await asyncio.create_subprocess_exec(
    *[
      FFPROBE_PATH,
      '-hide_banner',
      f'http://127.0.0.1:{HTTP_PORT}/{job_id}/{file_name}'
    ],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE
  )
  output, stderr = await proc.communicate()
  output = (
    f"{output.decode('utf8')}"
    f"\n{stderr.decode('utf8')}"
    f'\n(downloaded {file_jobs[job_id].bytes_downloaded // 1024} KB'
    f' in {round(time.time() - start_time, 1)}s)'
  )
  del file_jobs[job_id]

  if proc.returncode:
    output = f'ffprobe returned {proc.returncode}\n{output}'

  try:
    await event.respond(output, reply_to=target, parse_mode=parse_pre)
  except MessageTooLongError:
    await borg.send_file(
      await event.get_input_chat(),
      f'<pre>{output}</pre>'.encode('utf-8'),
      reply_to=target,
      attributes=[
        DocumentAttributeFilename('info.html')
      ],
      allow_cache=False
    )


async def on_init():
  global HTTP_PORT, unload

  app = web.Application()
  app.router.add_get('/{id}/{file_name}', http_handler)

  runner = web.AppRunner(app)
  await runner.setup()
  site = web.TCPSite(runner, '127.0.0.1', 0)
  await site.start()
  HTTP_PORT = site._server.sockets[0].getsockname()[1]
  logger.info(f'started http server on port {HTTP_PORT}')

  async def do_unload():
    await site.stop()
    await runner.shutdown()
    await app.cleanup()
    logger.info('stopped http server')

  unload = do_unload


asyncio.create_task(on_init())