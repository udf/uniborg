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

start_time = 1575375395
frame_time = 60 * 10
storage.img = storage.img or ''

files = [path.join('/home/sam/caxx/', f'f{i:04d}.png') for i in range(124, 3229)]
files.append('/home/sam/caxx/default.png')
if not all(path.isfile(f) for f in files):
    missing = [f for f in files if not path.isfile(f)]
    raise RuntimeError(f"Files are missing: {missing}\npls fix")


def crop_pp(im):
    w, h = im.size
    square_size = min(w, h)
    im = im.resize(
        (640, 640),
        resample=Image.LANCZOS,
        box=(
            (w - square_size) / 2,
            (h - square_size) / 2,
            (w + square_size) / 2,
            (h + square_size) / 2,
        )
    )
    return im


async def do_thing():
    while 1:
        await asyncio.sleep(30)

        elapsed = time.time() - start_time
        frame = min(floor(elapsed / frame_time), len(files) - 1)
        filename = files[frame]

        if storage.img == filename:
            continue
        logger.info(f'setting {filename}')

        im = crop_pp(Image.open(filename))
        f = BytesIO()
        im.save(f, format='png')
        del im
        f.seek(0)

        await borg(UploadProfilePhotoRequest(
            await borg.upload_file(f)
        ))
        del f

        storage.img = filename


asyncio.ensure_future(do_thing())
