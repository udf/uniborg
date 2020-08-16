"""
Converts stickers that you send into gifs that when sent are replaced by the
original sticker

Caveats:
- Files are only removed from cache if sending fails because the reference expired,
  this means cache can grow forever
"""
import asyncio
import subprocess
import struct
import re
from functools import partial
from tempfile import NamedTemporaryFile
from base64 import b64encode, b64decode

from uniborg.util import send_replacement_message

from telethon import tl, types, utils, events, errors
from telethon.tl.functions.messages import (
    SaveGifRequest,
    UploadMediaRequest
)
import ffmpeg

CHANNEL_ID = 1483189530

b64encode = partial(b64encode, altchars=b'+#')
b64decode = partial(b64decode, altchars=b'+#')
magic_filename_fmt = 'G2S{}.mp4'
magic_filename_re = re.compile(r'^G2S(.+)\.mp4$')
# msg_id, sticker_id
magic_filename_packed_fmt = '!qq'

# {id: InputDocument}
cache = storage.cache or {}

# {sticker id: gif id}
stickers_to_gifs = {int(k): v for k, v in (storage.stickers_to_gifs or {}).items()}


def cache_store(input_doc):
    cache[input_doc.id] = input_doc
    storage.cache = cache


def link_sticker_to_gif(sticker_id, gif_id):
    stickers_to_gifs[sticker_id] = gif_id
    storage.stickers_to_gifs = stickers_to_gifs


@borg.on(borg.admin_cmd('ss'))
async def on_save(event):
    await event.delete()
    target = await event.get_reply_message()
    if not target.sticker:
        return
    await on_sticker(target)


@borg.on(events.NewMessage(chats=borg.uid, outgoing=False))
@borg.on(events.NewMessage(outgoing=True))
async def on_sticker(event):
    if not event.sticker:
        return

    cache_store(utils.get_input_document(event.sticker))

    # try to fetch and (re)save the gif for this sticker if we have it
    gif_id = stickers_to_gifs.get(event.sticker.id, 0)
    gif_file = cache.get(gif_id, None)
    if gif_file:
        logger.info(f'(Re)saving cached GIF ({gif_id}) for {event.sticker.id}')
        try:
            await borg(SaveGifRequest(id=gif_file, unsave=False))
            return
        except errors.FileReferenceExpiredError:
            del cache[gif_id]

    logger.info(f'Converting {event.sticker.id}')
    infile = await borg.download_media(event.sticker, file=NamedTemporaryFile())

    # make mp4
    outfile = NamedTemporaryFile('rb')
    command = (
        ffmpeg.input('template.png')
        .overlay(
            ffmpeg.input(infile.name)
            .filter(
                'scale',
                w='512',
                h='512',
                force_original_aspect_ratio='decrease'
            ),
            x='(W-w)/2',
            y='(H-h)/2',
            shortest='1'
        )
        .output(
            outfile.name,
            f='mp4',
            vcodec='h264',
            pix_fmt='yuv420p',
            crf='18',
        )
        .overwrite_output()
        .compile()
    )

    # Hack to insert -f lavfi before input template
    i = command.index('template.png')
    command[i] = 'color=#282828:512x512'
    assert command[i - 1] == '-i'
    command.insert(i - 1, 'lavfi')
    command.insert(i - 1, '-f')

    subprocess.run(
        command,
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    infile.close()

    logger.info(f'Uploading gif for {event.sticker.id,}')
    msg = await borg.send_message(CHANNEL_ID, file=event.sticker)
    filename = magic_filename_fmt.format(
        b64encode(struct.pack(
            magic_filename_packed_fmt, msg.id, event.sticker.id
        )).decode('ascii')
    )
    uploaded_file = await borg.upload_file(
        outfile,
        file_name=filename,
        part_size_kb=512
    )
    outfile.close()
    media = await borg(UploadMediaRequest('me', uploaded_file))
    media = utils.get_input_document(media)

    cache_store(media)
    link_sticker_to_gif(event.sticker.id, media.id)

    logger.info(f'Saving {media.id} for {event.sticker.id}')
    await borg(
        SaveGifRequest(id=media, unsave=False)
    )


@borg.on(events.NewMessage(outgoing=True))
async def on_gif(event):
    if not event.gif:
        return

    m = magic_filename_re.match(event.file.name or '')
    if not m:
        return

    msg_id, sticker_id = struct.unpack(
        magic_filename_packed_fmt,
        b64decode(m.group(1))
    )
    if not msg_id:
        return

    await event.delete()

    # try to send from cache
    sticker_file = cache.get(sticker_id, None)
    if sticker_file:
        logger.info(f'Sending cached sticker for {sticker_id}')
        try:
            await send_replacement_message(event, file=sticker_file)
            return
        except errors.FileReferenceExpiredError:
            logger.info(f'Cache expired for {sticker_id}')
            del cache[sticker_id]

    # try to get message and send sticker
    logger.info(f'Fetching message #{msg_id} for {sticker_id}')
    msg = await borg.get_messages(CHANNEL_ID, ids=msg_id)
    if msg:
        cache_store(utils.get_input_document(msg.sticker))
        await send_replacement_message(event, file=msg.sticker)
        return

    logger.info(f'Message #{msg_id} not found, unsaving #{event.gif.id}')
    for sticker_id, gif_id in stickers_to_gifs.items():
        if gif_id == event.gif.id:
            del stickers_to_gifs[sticker_id]
            break
    storage.stickers_to_gifs = stickers_to_gifs
    await borg(
        SaveGifRequest(id=event.gif, unsave=True)
    )


async def on_init():
    logger.info('Getting channel')
    await borg.get_dialogs()
    try:
        channel = await borg.get_input_entity(CHANNEL_ID)
        logger.info(f'Got channel: {repr(channel)}')
    except Exception as e:
        logger.info('Error getting channel: {e}')

    # TODO: fetch saved gifs if we start needing file reference to save a gif


asyncio.ensure_future(on_init())