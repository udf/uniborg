"""
Reply to a file with .f to send it as a photo
"""
from io import BytesIO

from stdplugins.kbass_core import self_reply_cmd
from telethon import types
from telethon.errors import PhotoInvalidDimensionsError


@self_reply_cmd(borg, r"^\.f$")
async def on_file_to_photo(event, target):
    try:
        image = target.media.document
    except AttributeError:
        return
    if not image.mime_type.startswith('image/'):
        return  # This isn't an image
    if image.mime_type == 'image/webp':
        return  # Telegram doesn't let you directly send stickers as photos
    if image.size > 10 * 1024 * 1024:
        return  # We'd get PhotoSaveFileInvalidError otherwise

    file = await borg.download_media(target, file=BytesIO())
    file.seek(0)
    img = await borg.upload_file(file)

    try:
        await event.respond(
            reply_to=target,
            file=types.InputMediaUploadedPhoto(img)
        )
    except PhotoInvalidDimensionsError:
        return
