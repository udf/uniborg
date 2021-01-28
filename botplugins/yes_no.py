r"""Adding "yes or no" to the end of your message will result in a yes or no answer from the bot.
Also supports "y/n", and other alternatives.

pattern:  `(?i)(yes|y)(/| or )(no|n)\??$`
"""

import re
from random import choice
from telethon import events
from uniborg.util import edit_blacklist


# Yes or no
# Matches "y/n" "yes or no" "yes/no?" etc
@borg.on(events.NewMessage(
    pattern=re.compile(r"(?i)(yes|y)(/| or )(no|n)\??$").search, forwards=False))
async def yes_or_no(event):
    blacklist = storage.blacklist or set()
    if event.chat_id in blacklist:
        return

    await event.reply(choice(("Yes.", "No.")))


@borg.on(borg.admin_cmd(r"(r)?blacklist", r"(?P<shortname>\w+)"))
async def blacklist(event):
    m = event.pattern_match
    shortname = m["shortname"]

    if shortname not in __file__:
        return

    storage.blacklist = edit_blacklist(event.chat_id, storage.blacklist, m.group(1))
    await event.reply("Updated blacklist.")
