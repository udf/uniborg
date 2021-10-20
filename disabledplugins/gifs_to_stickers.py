"""
Converts stickers that you send into gifs that when sent are replaced by the
original sticker
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

convert_keys_to_int = lambda d: {int(k): v for k, v in d.items()}
b64encode = partial(b64encode, altchars=b'+#')
b64decode = partial(b64decode, altchars=b'+#')

magic_filename_fmt = 'G2S{}.mp4'
magic_filename_re = re.compile(r'^G2S(.+)\.mp4$')
magic_filename_packed_fmt = '!q'  # sticker_id

# {id: InputDocument}
cache = convert_keys_to_int(storage.cache or {})

# {file id: msg id}
file_msg_ids = convert_keys_to_int(storage.file_msg_ids or {})

# {sticker id: gif id}
stickers_to_gifs = convert_keys_to_int(storage.stickers_to_gifs or {})


async def store_file(document):
    input_doc = utils.get_input_document(document)
    logger.info(f'Caching {input_doc.id}')
    cache[input_doc.id] = input_doc
    storage.cache = cache

    if input_doc.id in file_msg_ids:
        return

    logger.info(f'Saving message for #{input_doc.id}')
    msg = await borg.send_message(CHANNEL_ID, file=input_doc)
    file_msg_ids[input_doc.id] = msg.id
    storage.file_msg_ids = file_msg_ids


async def try_with_stored_file(file_id, action):
    input_doc = cache.get(file_id, None)
    if input_doc:
        try:
            return await action(input_doc)
        except errors.FileReferenceExpiredError:
            logger.info(f'Cache expired for #{file_id}')
            pass

    msg_id = file_msg_ids.get(file_id, None)
    if not msg_id:
        logger.error(f'No saved message associated with #{file_id}!')
        return

    logger.info(f'Fetching message #{msg_id} for #{file_id}')
    msg = await borg.get_messages(CHANNEL_ID, ids=msg_id)
    if not msg:
        logger.error(f'Message #{msg_id} for #{file_id} not found!')
        del file_msg_ids[msg_id]
        storage.file_msg_ids = file_msg_ids
        return

    await store_file(msg.document)
    input_doc = utils.get_input_document(msg.document)
    return await action(input_doc)


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

    await store_file(event.sticker)

    # try to fetch and (re)save the gif for this sticker if we have it
    gif_id = stickers_to_gifs.get(event.sticker.id, 0)
    if gif_id:
        logger.info(f'(Re)saving GIF #{gif_id} for #{event.sticker.id}')
        success = await try_with_stored_file(
            gif_id,
            lambda f: borg(SaveGifRequest(id=f, unsave=False))
        )
        if success:
            return

    logger.info(f'Converting #{event.sticker.id}')
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

    logger.info(f'Uploading GIF for #{event.sticker.id}')
    filename = magic_filename_fmt.format(
        b64encode(struct.pack(magic_filename_packed_fmt, event.sticker.id)).decode('ascii')
    )
    uploaded_file = await borg.upload_file(
        outfile,
        file_name=filename,
        part_size_kb=512
    )
    outfile.close()
    media = await borg(UploadMediaRequest('me', uploaded_file))
    media = utils.get_input_document(media)

    await store_file(media)
    link_sticker_to_gif(event.sticker.id, media.id)

    logger.info(f'Saving GIF #{media.id} for #{event.sticker.id}')
    await borg(SaveGifRequest(id=media, unsave=False))


@borg.on(events.NewMessage(outgoing=True))
async def on_gif(event):
    if not event.gif:
        return

    m = magic_filename_re.match(event.file.name or '')
    if not m:
        return

    sticker_id, = struct.unpack(
        magic_filename_packed_fmt,
        b64decode(m.group(1))
    )

    await event.delete()

    # try to send from cache/saved message
    logger.info(f'Sending saved sticker #{sticker_id} for #{event.gif.id}')
    msg = await try_with_stored_file(
        sticker_id,
        lambda f: send_replacement_message(event, file=f)
    )
    if msg:
        await store_file(event.gif)
        return

    logger.info(f'Saved message for #{sticker_id} not found, unsaving gif #{event.gif.id}')
    for sticker_id, gif_id in stickers_to_gifs.items():
        if gif_id == event.gif.id:
            del stickers_to_gifs[sticker_id]
            break
    storage.stickers_to_gifs = stickers_to_gifs
    await borg(SaveGifRequest(id=event.gif, unsave=True))


async def on_init():
    logger.info('Getting channel')
    await borg.get_dialogs()
    try:
        channel = await borg.get_input_entity(CHANNEL_ID)
        logger.info(f'Got channel: {repr(channel)}')
    except Exception as e:
        logger.info('Error getting channel: {e}')


asyncio.ensure_future(on_init())