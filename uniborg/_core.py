# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import asyncio
import traceback

from uniborg import util

DELETE_TIMEOUT = 2


@borg.on(util.admin_cmd(r"^\.(?:(?:re)?load|enable|add) (?P<shortname>\w+)$"))
async def load_reload(event):
    await event.delete()
    shortname = event.pattern_match["shortname"]

    try:
        if shortname in borg._plugins:
            await borg.remove_plugin(shortname)
        borg.load_plugin(shortname)

        msg = await event.respond(
            f"Successfully (re)loaded plugin {shortname}")
        await asyncio.sleep(DELETE_TIMEOUT)
        await borg.delete_messages(msg.to_id, msg)

    except Exception as e:
        tb = traceback.format_exc()
        logger.warn(f"Failed to (re)load plugin {shortname}: {tb}")
        await event.respond(f"Failed to (re)load plugin {shortname}: {e}")


@borg.on(util.admin_cmd(r"^\.(?:unload|disable|remove) (?P<shortname>\w+)$"))
async def remove(event):
    await event.delete()
    shortname = event.pattern_match["shortname"]

    if shortname == "_core":
        msg = await event.respond(f"Not removing {shortname}")
    elif shortname in borg._plugins:
        await borg.remove_plugin(shortname)
        msg = await event.respond(f"Removed plugin {shortname}")
    else:
        msg = await event.respond(f"Plugin {shortname} is not loaded")

    await asyncio.sleep(DELETE_TIMEOUT)
    await borg.delete_messages(msg.to_id, msg)
