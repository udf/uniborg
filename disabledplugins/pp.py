# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import asyncio
import time
from io import BytesIO
from math import floor
from os import path

from telethon.tl.functions.photos import UploadProfilePhotoRequest
from PIL import Image

start_time = 1597622400
frame_time = 60 * 60 * 24
storage.img = storage.img or ''

files = [path.join('/home/sam/pp/', f'{i:02d}.mp4') for i in range(30)]
if not all(path.isfile(f) for f in files):
    missing = [f for f in files if not path.isfile(f)]
    raise RuntimeError(f"Files are missing: {missing}\npls fix")

end_time = start_time + frame_time * len(files)

def fmap(value, istart, istop, ostart, ostop):
    return ostart + (ostop - ostart) * ((value - istart) / (istop - istart))


async def do_thing():
    while 1:
        await asyncio.sleep(10)

        frame = fmap(time.time(), start_time, end_time, 0, len(files) - 1)
        frame = min(floor(frame), len(files) - 1)
        if frame < 0:
            continue

        filename = files[frame]

        if storage.img == filename:
            continue
        logger.info(f'Setting {filename}')

        f = await borg.upload_file(filename)
        await borg(UploadProfilePhotoRequest(video=f))

        storage.img = filename


asyncio.ensure_future(do_thing())
