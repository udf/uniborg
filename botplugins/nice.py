"""Nice

Keeps track of instances of the word "nice"
Use `/nice` to see all nices, and `/ripnice` to reset your stats.

patterns:
• `(?<!/)\\bno*i+c+e+\\b`
• `/nice`
• `/ripnice (yes)?`
• `/(not|very)nice (\d+)` ADMIN ONLY
"""

import re
import html
from asyncio import sleep

from telethon import events
from uniborg.util import blacklist


@borg.on(borg.cmd(r"(me)?nice"))
async def return_nice(event):
    nices = storage.nices
    match = event.pattern_match.string

    reply_msg = "<b>Nice</b>"

    sender = str(event.sender_id)
    try:
        if "me" in match:
            nices = {sender: nices[sender]}
    except KeyError:
        msg = await event.reply("No nice found.  Not nice.")

        await sleep(5)

        await msg.delete()
        try:
            await event.delete()
        except:
            pass

        return

    for user in nices.values():
        name = html.escape(user["name"])
        count = user["count"]

        reply_msg += f"\n{name}:  <code>{count}</code>"

    await event.respond(reply_msg, parse_mode="html")


@borg.on(borg.admin_cmd(r"(not|very)nice", pattern=r"(\d+)"))
async def nice_blacklist(event):
    m = event.pattern_match
    id = m.group(2)
    action = m.group(1)
    nice_blacklist = storage.nice_blacklist or set()

    if "not" in action:
        nice_blacklist.add(id)
    elif "very" in action:
        nice_blacklist.discard(id)

    storage.nice_blacklist = nice_blacklist
    msg = await event.respond("Nice blacklist updated.")
    await sleep(5)
    await msg.delete()


@borg.on(borg.cmd(r"ripnice\s*(yes)?"))
async def remove_nice(event):
    m = event.pattern_match
    if not m.group(1):
        await event.reply("Are you sure?  Respond with `/ripnice yes`.")
        return


    sender_id = str(event.sender_id)
    nices = storage.nices or {}

    nices.pop(sender_id)

    msg = await event.respond(f"RIP {event.sender.first_name}\nNice.")


# count nices
@borg.on(events.NewMessage(pattern=re.compile(r"(?<!/)\bno*i+c+e+r*\b").findall))
async def nice(event):
    blacklist = storage.blacklist or set()
    if event.chat_id in blacklist:
        return

    if event.is_private:
        return

    m = event.pattern_match
    sender_id = str(event.sender_id)
    count = len(m)

    nice_blacklist = storage.nice_blacklist or {}
    if sender_id in nice_blacklist:
        return

    sender = await event.get_sender()
    name = sender.first_name

    nices = storage.nices or {}
    nices_user = nices.get(sender_id)
    if not nices_user:
        total_count = 0
    else:
        total_count = int(nices_user["count"])

    nices[sender_id] = {"name": name, "count": str(total_count + count)}
    storage.nices = nices


@borg.on(borg.blacklist_plugin())
async def on_blacklist(event):
    storage.blacklist = await blacklist(event, storage.blacklist)
