"""
Reply to audio with .vn (or put .vn in the caption) to resend it as a voice message
"""

import asyncio
from asyncio import subprocess
from os import path
from tempfile import NamedTemporaryFile

from telethon.tl.types import DocumentAttributeAudio, DocumentAttributeFilename
import numpy as np
import ffmpeg


# durov pls fix server waveforms
async def generate_waveform(filename, duration):
  # speedup audio to ~1s
  ratio = duration / 1

  # apply multiple speedup filters each ≤ 10x for accuracy
  nth_root = 1
  while (final_ratio := ratio ** (1/nth_root)) > 10:
    nth_root += 1

  graph = ffmpeg.input(filename).audio
  if final_ratio > 1:
    for _ in range(nth_root):
      graph = graph.filter('atempo', final_ratio)

  cmd = graph.output(
    '-',
    ac=1,
    ar=16000,
    acodec='pcm_s8',
    f='data'
  ).compile()

  proc = await asyncio.create_subprocess_exec(*cmd, stdout=subprocess.PIPE)
  stdout, stderr = await proc.communicate()

  # interpolate and normalize 100 samples
  data = np.abs(np.int16(np.frombuffer(stdout, dtype=np.int8)))

  waveform = np.interp(
    np.arange(1, 101) * (len(data) / 101),  # avoid taking samples at the ends
    np.arange(0, len(data)),
    data
  )
  waveform = (waveform / np.max(waveform) * 31)

  # convert to bytes containing 100 consecutive 5-bit numbers
  bits = ''.join(f'{round(i):05b}' for i in waveform)
  return bytes(int(f'{bits[i:i+8]:0<8}', 2) for i in range(0, len(bits), 8))


@borg.on(borg.admin_cmd(r'vn(d)?'))
async def on_audio_to_vn(event):
  await event.delete()
  target = event.message
  should_delete = True
  if not target.media:
    target = await event.get_reply_message()
    should_delete = target.out and event.pattern_match.group(1)
  if not target.media:
    return

  infile = await borg.download_media(target, file=NamedTemporaryFile(suffix='.opus'))
  infile.seek(0)
  probe = ffmpeg.probe(infile.name)

  audio_streams = [stream for stream in probe['streams'] if stream['codec_type'] == 'audio']
  if not audio_streams:
    logger.info(f'No audio streams found in {target.sender_id}/{target.id} ({target.file.name})')
    infile.close()
    return

  # certain formats dont work as voice messages
  outfile = infile
  if audio_streams[0]['codec_name'] != 'opus':
    outfile = NamedTemporaryFile('rb', suffix='.opus')
    cmd = (
      ffmpeg
      .input(infile.name).audio
      .output(
        outfile.name,
        ac='1',
        f='opus',
        acodec='libopus',
        audio_bitrate='128k',
        vbr='on'
      )
      .overwrite_output()
      .compile()
    )
    proc = await asyncio.create_subprocess_exec(*cmd)
    await proc.wait()

  duration = float(audio_streams[0]['duration'])

  await borg.send_file(
    await event.get_input_chat(),
    file=outfile,
    attributes=[
      DocumentAttributeAudio(
        duration=round(duration),
        voice=True,
        waveform=await generate_waveform(infile.name, duration)
      ),
      DocumentAttributeFilename('')
    ]
  )

  outfile.close()

  if should_delete:
    await target.delete()