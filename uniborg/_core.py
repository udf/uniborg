# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import asyncio
import traceback

DELETE_TIMEOUT = 2


@borg.on(borg.admin_cmd(r"(?:re)?load", r"(?P<shortname>\w+)"))
async def load_reload(event):
    if not borg.me.bot:
        await event.delete()
    shortname = event.pattern_match["shortname"]

    try:
        if shortname in borg._plugins:
            await borg.remove_plugin(shortname)
        borg.load_plugin(shortname)

        msg = await event.respond(
            f"Successfully (re)loaded plugin {shortname}")
        if not borg.me.bot:
            await asyncio.sleep(DELETE_TIMEOUT)
            await borg.delete_messages(msg.to_id, msg)

    except Exception as e:
        tb = traceback.format_exc()
        logger.warn(f"Failed to (re)load plugin {shortname}: {tb}")
        await event.respond(f"Failed to (re)load plugin {shortname}: {e}")


@borg.on(borg.admin_cmd(r"(?:unload|disable|remove)", r"(?P<shortname>\w+)"))
async def remove(event):
    if not borg.me.bot:
        await event.delete()
    shortname = event.pattern_match["shortname"]

    if shortname == "_core":
        msg = await event.respond(f"Not removing {shortname}")
    elif shortname in borg._plugins:
        await borg.remove_plugin(shortname)
        msg = await event.respond(f"Removed plugin {shortname}")
    else:
        msg = await event.respond(f"Plugin {shortname} is not loaded")

    if not borg.me.bot:
        await asyncio.sleep(DELETE_TIMEOUT)
        await borg.delete_messages(msg.to_id, msg)


@borg.on(borg.cmd(r"plugins?(?: (?P<shortname>\w+))?"))
@borg.on(borg.cmd(r"help(?: (?P<shortname>\w+))?"))
async def help(event):
    if borg.me.bot and not event.is_private:
        return

    shortname = event.pattern_match["shortname"]
    plugin_dict = {}

    for name, mod in sorted(borg._plugins.items(), key=lambda t: t[0]):
        if name == "_core":
            continue
        desc = (mod.__doc__ or "No Description")
        plugin_dict[name] = desc

    plugin_list = "`\n• `".join(plugin_dict)

    if not shortname:
        result = f"**Plugins:**  "
        if not borg.me.bot:
            result += str(len(borg._plugins))

        result += f"\n• `{plugin_list}` \
                  \n\nSend `/help plugin_name` for more information."
    else:
        result = plugin_dict[shortname]

    if not borg.me.bot:
        await event.edit(result)
    else:
        await event.reply(result)
