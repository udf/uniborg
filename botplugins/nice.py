"""Nice

Keeps track of instances of the word "nice"
Use `/nice` to see all nices, and `/ripnice` to reset your stats.

patterns:
• `(?<!/)\\bn+o*i+c+e+\\b`
• `/nice`
• `/ripnice (yes)?`
• `/(not|very)nice (\d+)` ADMIN ONLY
"""

import re
import html
from asyncio import sleep
from operator import itemgetter
from collections import defaultdict

from telethon import events
from uniborg.util import blacklist, cooldown


# print nice leaderboard
@borg.on(borg.cmd(r"(me)?nice"))
@cooldown(15)
async def return_nice(event):
    users = storage.users or {}
    groups = storage.groups or {}
    match = event.pattern_match.string

    reply_msg = "<b>Nice</b>"

    sender = str(event.sender_id)
    try:
        if "me" in match:
            users = {sender: users[sender]}
    except KeyError:
        msg = await event.reply("No nice found.  Not nice.")

        await sleep(5)
        await msg.delete()

        try:
            await event.delete()
        except:
            pass
        return

    chat_id = str(event.chat_id)
    if not chat_id in groups:
        try:
            await event.delete()
        except:
            pass
        return

    group_users = {}
    for user in groups[chat_id]:
        try:
            group_users[user] = users[user]
        except KeyError:
            pass

    if not group_users:
        try:
            await event.delete()
        except:
            pass
        return

    sorted_users = dict(sorted(group_users.items(), key=lambda i: (i[1]["count"]), reverse=True))
    for user in sorted_users.values():
        try:
            name = html.escape(user["name"])
        except AttributeError:
            pass
        count = user["count"]

        reply_msg += f"\n{name}:  <code>{count}</code>"

    await event.respond(reply_msg, parse_mode="html")


# blacklist someone from having their score reported
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


# remove someone from the leaderboard
@borg.on(borg.admin_cmd(r"ripnice\s*(\d+)?"))
@borg.on(borg.cmd(r"ripnice\s*(yes)?"))
async def remove_nice(event):
    m = event.pattern_match
    if not m.group(1):
        await event.reply("Are you sure?  Respond with `/ripnice yes`.")
        return

    arg = m.group(1)

    member = str(event.sender_id)

    if arg != "yes":
        member = arg
    users = storage.users or {}

    try:
        name = users[member]["name"]
        users[member]["count"] = 0
    except KeyError:
        return

    storage.users = users

    msg = await event.respond(f"RIP {name}\nNice.")


# count nices
@borg.on(events.NewMessage(pattern=re.compile(r"(?i)(?<!/)\bn+o*i+c+e+r*\b").findall))
@cooldown(15, chat=False)
async def nice(event):
    blacklist = storage.blacklist or set()
    if event.chat_id in blacklist:
        return

    if event.is_private:
        return

    sender_id = str(event.sender_id)

    nice_blacklist = storage.nice_blacklist or {}
    if sender_id in nice_blacklist:
        return

    sender = await event.get_sender()
    name = sender.first_name
    m = event.pattern_match
    count = len(m)
    if count > 15:
        count = -count
    if count > 5:
        count = -1
    chat_id = str(event.chat_id)

    users = storage.users or defaultdict(lambda: defaultdict(int))
    groups = storage.groups or defaultdict(set)

    user = users[sender_id]
    user["count"] = int(user["count"]) + count
    user["name"] = name

    chat = groups[chat_id]
    chat.add(sender_id)

    storage.users = users
    storage.groups = groups


@borg.on(borg.blacklist_plugin())
async def on_blacklist(event):
    storage.blacklist = await blacklist(event, storage.blacklist)
