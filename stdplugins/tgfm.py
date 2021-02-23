"""
Sync your bio with lastfm.  Now playing songs will replace your bio.
You can also add a static bio prefix and suffix.
.sb[pbmds] (prefix, bio middle default, suffix) to set the bio
.bio to view the bio
"""

import aiohttp
import asyncio
from telethon import events, utils
# bio related stuff
from telethon.tl.functions.account import UpdateProfileRequest
from telethon.tl.functions.users import GetFullUserRequest

api = "http://ws.audioscrobbler.com/2.0"
bio = storage.bio or {"prefix": "", "middle": "", "suffix": ""}
fm_api_key = storage.fm_api_key or ""
username = storage.fm_username or "qwertyspace"

import logging
logging.basicConfig(level=logging.WARNING)


async def check_bio():
    full = await borg(GetFullUserRequest("me"))
    return full.about


async def reset_bio():
    await update_bio(bio["middle"])


async def update_bio(new_bio):
    curr_bio = await check_bio()
    length = 70 - len(bio["prefix"]) - len(bio["suffix"]) - 1

    if len(new_bio) > length:
        new_bio = new_bio[:length] + "…"

    full_bio = bio["prefix"] + new_bio + bio["suffix"]

    if full_bio == curr_bio:
        return

    await borg(UpdateProfileRequest(about=full_bio))


async def check_np(session):
    params = {"method": "user.getrecenttracks",
             "limit": "1", "user": username,
             "api_key": fm_api_key, "format": "json"}

    async with session.get(api, params=params) as resp:
        json = await resp.json()
        try:
            track = json["recenttracks"]["track"][0]
        except KeyError, IndexError:
            return None

    if "@attr" in track and track["@attr"]["nowplaying"]:
        artist = track["artist"]["#text"]
        title = track["name"]
        return f"{artist} - {title}"

    return None


@borg.on(borg.cmd(r"s(?:et)?b(?:io)? ?([pbmds])? (.+)"))
async def set_bio(event):
    m = event.pattern_match
    arg = m.group(1)
    val = m.group(2)

    val.replace(r"\s", " ")

    if r"\r" in val:
        val = ""

    async def bio_err(new_bio):
        await event.edit(f'Bio:  "{new_bio}" is too long!  ({len(new_bio)} chars)\n \
                        A bio must be ≤70 characters.')
        await asyncio.sleep(10)

    if arg == "p":
        new_bio = val + bio["middle"] + bio["suffix"]
        if len(new_bio) > 70:
           await bio_err(new_bio)

        bio["prefix"] = val

    if not arg or arg in "bmd":
        new_bio = bio["prefix"] + val + bio["suffix"]
        if len(new_bio) > 70:
            await bio_err(new_bio)

        bio["middle"] = val

    if arg == "s":
        new_bio = bio["prefix"] + bio["middle"] + val
        if len(new_bio) > 70:
            await bio_err(new_bio)

        bio["suffix"] = val

    await event.delete()
    storage.bio = bio
    await reset_bio()


@borg.on(borg.cmd(r"bio"))
async def send_bio(event):
    await event.edit("**Bio:**  " + "".join(bio.values()))


import traceback
async def main():
    try:
        async with aiohttp.ClientSession() as session:
            while True:
                await asyncio.sleep(15)
                np = await check_np(session)

                if not np:
                    await reset_bio()
                    await asyncio.sleep(15)
                    continue
                else:
                    new_bio = f"Listening to " + np
                    await update_bio(new_bio)
                    continue
    except Exception:
        traceback.print_exc()


if not fm_api_key:
    fm_api_key = input("lastfm API key:  ")
    storage.fm_api_key = fm_api_key


async def unload():
    if main_loop:
        main_loop.cancel()
        await reset_bio()


loop = asyncio.get_event_loop()
main_loop = loop.create_task(main())
