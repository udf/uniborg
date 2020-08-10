"""
Converts stickers that you send into gifs that when sent are replaced by the
original sticker

Caveats:
- Plain webp files will be re-uploaded if they are not in the cache
  (the same is true for stickers which get deleted from their pack)
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
from io import BytesIO

from uniborg.util import send_replacement_message

from telethon import tl, types, utils, events, errors
from telethon.tl.functions.messages import (
    GetStickerSetRequest,
    GetSavedGifsRequest,
    SaveGifRequest,
    UploadMediaRequest
)
import ffmpeg
from basest.encoders import Encoder

b64encode = partial(b64encode, altchars=b'+#')
b64decode = partial(b64decode, altchars=b'+#')
magic_filename_fmt = 'G2S{}.mp4'
magic_filename_re = re.compile(r'^G2S(.+)\.mp4$')
# sticker id, sticker set id, sticker set hash
magic_filename_packed_fmt = '!qqq'

class Base126(Encoder):
    input_base = 256
    output_base = 126
    input_ratio = 13
    output_ratio = 15
    input_symbol_table = list(bytes(range(256)))
    output_symbol_table = [chr(i + 1) for i in range(126)]
    padding_symbol = chr(127)

base126 = Base126()

# {id: InputDocument}
cache = {}

# {sticker id: gif id}
stickers_to_gifs = {int(k): v for k, v in (storage.stickers_to_gifs or {}).items()}


def cache_store(input_doc):
    cache[input_doc.id] = input_doc


def link_sticker_to_gif(sticker_id, gif_id):
    stickers_to_gifs[sticker_id] = gif_id
    storage.stickers_to_gifs = stickers_to_gifs


async def upload_gif(file, sticker_id, pack_id=0, pack_hash=0):
    logger.info(f'Uploading gif for {sticker_id}')
    filename = magic_filename_fmt.format(
        b64encode(
            struct.pack(magic_filename_packed_fmt, sticker_id, pack_id, pack_hash)
        ).decode('ascii')
    )
    uploaded_file = await borg.upload_file(
        file,
        file_name=filename,
        part_size_kb=512
    )
    media = await borg(UploadMediaRequest('me', uploaded_file))
    media = utils.get_input_document(media)

    cache_store(media)
    link_sticker_to_gif(sticker_id, media.id)

    logger.info(f'Saving {media.id} for {sticker_id}')
    await borg(
        SaveGifRequest(id=media, unsave=False)
    )


def unpack_filename(filename):
    m = magic_filename_re.match(filename or '')
    if not m:
        return

    data = struct.unpack(
        magic_filename_packed_fmt,
        b64decode(m.group(1))
    )
    return data


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
            await borg(
                SaveGifRequest(id=gif_file, unsave=False)
            )
            return
        except errors.FileReferenceExpiredError:
            del cache[gif_id]

    logger.info(f'Downloading {event.sticker.id}')
    # download and pack sticker data
    infile = NamedTemporaryFile()
    await borg.download_media(event.sticker, file=infile)
    infile.seek(0)
    comment = ''.join(base126.encode(infile.read()))

    logger.info(f'Converting {event.sticker.id}')
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
            metadata=f'comment={comment}'
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

    sticker_set = event.file.sticker_set
    pack_info = tuple()
    if hasattr(sticker_set, 'id'):
        pack_info = (sticker_set.id, sticker_set.access_hash)

    await upload_gif(outfile, event.sticker.id, *pack_info)
    outfile.close()


@borg.on(events.NewMessage(outgoing=True))
async def on_gif(event):
    if not event.gif:
        return
    data = unpack_filename(event.file.name)
    if not data:
        return

    await event.delete()
    sticker_id, pack_id, pack_hash = data

    # try to send from cache
    sticker_file = cache.get(sticker_id, None)
    if sticker_file:
        logger.info(f'Sending cached sticker for {sticker_id}')
        try:
            await send_replacement_message(event, file=sticker_file)
            link_sticker_to_gif(m.sticker.id, event.gif.id)
            return
        except errors.FileReferenceExpiredError:
            logger.info(f'Cache expired for {sticker_id}')
            del cache[sticker_id]

    # try to get pack and find sticker in there
    try:
        if not pack_id:
            raise FileNotFoundError
        logger.info(f'Fetching pack {pack_id} for {sticker_id}')
        pack = await borg(
            GetStickerSetRequest(
                types.InputStickerSetID(pack_id, pack_hash)
            )
        )

        num_cached = 0
        for document in pack.documents:
            if document.id in stickers_to_gifs or document.id == sticker_id:
                cache_store(utils.get_input_document(document))
                num_cached += 1
        logger.info(
            f'Cached {num_cached}/{len(pack.documents)} stickers '
            f'from {pack.set.short_name} ({pack_id})'
        )

        sticker_file = cache.get(sticker_id, None)
        if not sticker_file:
            raise FileNotFoundError
        logger.info(f'Sending sticker ({sticker_id}) from fetched pack')
        await send_replacement_message(event, file=sticker_file)
        # add link in case this gif was not present when we fetched saved gifs
        link_sticker_to_gif(sticker_id, event.gif.id)
        return
    except (errors.StickersetInvalidError, FileNotFoundError):
        pass

    # download file and unpack comment data (webp file)
    logger.info(f'Downloading mp4 ({event.gif.id})')
    gif_file = NamedTemporaryFile()
    await borg.download_media(event.gif, file=gif_file)
    data = ffmpeg.probe(gif_file.name)
    tags = data['format']['tags']
    comment = tags.get('comment')
    if not comment:
        return

    webp = bytes(base126.decode(comment))

    logger.info(f'Sending raw webp data for {event.gif.id}')
    sticker_file = BytesIO(webp)
    sticker_file.name = 'sticker.webp'
    m = await send_replacement_message(event, file=sticker_file)
    cache_store(utils.get_input_document(m.sticker))

    # Re-upload existing gif with a new name
    # so that it points to the sticker we just uploaded
    gif_file.seek(0)
    await upload_gif(gif_file, m.sticker.id)
    await borg(
        SaveGifRequest(id=event.gif, unsave=True)
    )


async def fetch_saved_gifs():
    # Add saved gifs to cache, so that we can resave them when we
    # get the corresponding sticker
    saved_gifs = await borg(GetSavedGifsRequest(0))

    with storage.bulk_save():
        count = 0
        for gif in saved_gifs.gifs:
            name = tl.custom.file.File(gif).name
            data = unpack_filename(name)
            if not data:
                continue
            cache_store(utils.get_input_document(gif))
            sticker_id, pack_id, pack_hash = data
            link_sticker_to_gif(sticker_id, gif.id)
            count += 1

    storage.stickers_to_gifs = stickers_to_gifs
    logger.info(f'Loaded {count} items from saved gifs')


asyncio.ensure_future(fetch_saved_gifs())