"""Whitelist (BOT ADMIN ONLY)

The bot will only stay in groups in the whitelist.

Add groups to the whitelist with `/awhitelist -100123456789:Group Name`, and remove \
from the whitelist with `/awhitelist -100123456789`.

View the whitelist with `/whitelist`
"""


from asyncio import sleep
from uniborg.util import cooldown
from telethon import client, events, errors, utils


whitelist = storage.whitelist or {}


# Check groups
@borg.on(events.NewMessage(incoming=True,
                func=lambda e: not e.is_private))
async def check(event):
    if f"{event.chat_id}" in whitelist:
        return

    res = await event.respond("Chat not in whitelist.  Leaving.")
    await event.client.kick_participant(event.chat, "me")

    await sleep(5)
    try:
        await event.client.delete_messages(
            event.chat, res
        )
    except errors.ChannelPrivateError:
        pass


# Show the whitelist
@borg.on(borg.admin_cmd(r"whitelist"))
async def view_whitelist(event):
    reply_msg = ""

    for id in whitelist:
        reply_msg += f"\n`{id}`:  **{whitelist[id]}**"

    await event.reply(reply_msg)


# Add or remove groups from the whitelist
@borg.on(borg.admin_cmd(r"(a|r)whitelist (-100\d+)(?::\s*([\S ]+))?"))
async def modify_whitelist(event):
    m = event.pattern_match

    action = m.group(1)
    whitelist_id = m.group(2)
    try:
        whitelist_name = m.group(3)
    except AttributeError:
        whitelist_name = False

    if action == "r":
        msg = await event.reply(f"Removing '{whitelist[whitelist_id]}' from the whitelist...")
        whitelist.pop(whitelist_id)
    elif action == "a" and not whitelist_name:
        await event.reply("Please specify a group name. \
            Example:  `/awhitelist -100123456789:Group Name`")
    elif action == "a" and whitelist_name:
        msg = await event.reply(f"Adding **'{whitelist_name}'** to the whitelist...")
        whitelist[whitelist_id] = whitelist_name

    await sleep(1)
    storage.whitelist = whitelist
    await msg.edit(msg.text + "\n**Success!**")
