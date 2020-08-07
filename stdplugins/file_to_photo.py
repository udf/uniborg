"""
Reply to a file with .f to send it as a photo
Use .fd to delete the file (only works if you sent the file)
"""
import asyncio
from io import BytesIO
import concurrent.futures

from PIL import Image

from telethon.errors import PhotoInvalidDimensionsError


executor = concurrent.futures.ThreadPoolExecutor()


# From: https://github.com/Qwerty-Space/tanyabot/blob/d481c43baceffa2600aee950b33b23e52e10aa2c/plugins/global_functions.py
def downscale(fp, max_w=1280, max_h=1280, format="PNG"):
    im = Image.open(fp)
    resolution = im.size
    outfile = BytesIO()

    im.thumbnail((max_w, max_h), Image.LANCZOS)
    im.save(outfile, format)
    outfile.seek(0)

    return outfile


@borg.on(borg.admin_cmd(r"f(d)?"))
async def on_file_to_photo(event):
    await event.delete()
    target = await event.get_reply_message()
    try:
        image = target.media.document
    except AttributeError:
        return
    if not image.mime_type.startswith('image/'):
        return

    file = await borg.download_media(target, file=BytesIO())
    file.seek(0)
    im = await asyncio.get_running_loop().run_in_executor(
        executor,
        lambda: downscale(file)
    )

    im.name = "image.png"
    should_delete = (target.from_id == borg.uid and event.pattern_match.group(1))

    try:
        await borg.send_message(
            await event.get_input_chat(),
            file=im,
            reply_to=None if should_delete else target
        )

        if should_delete:
            await target.delete()
    except PhotoInvalidDimensionsError:
        return
