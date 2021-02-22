r"""Mein Führer!

When a user mentions Hitler, or the Führer, the bot will respond with one of a few stickers.
Limited to once a minute.

This is meant as a joke, mainly to relieve tension in heated arguments.
In no way do we support Hitler's or the Nazi party's ideals.



pattern:  `(?i)\b(hitler|f[uü]hrer)\b"` __(global)__
"""

import re
from random import choice
from telethon import events
from uniborg.util import cooldown, blacklist

responses = ["CAADAgADWgADraG3CP76-OQcP7msAg", # Tanya
             "CAADBAADkQYAAhgwqgVYHov8PqiL9gI", # The Professor
             "CAADAgADRQADqh-tD2oBxZyI7uVhAg" # Azunyan
            ]

# MEIN FÜHRER!
@borg.on(events.NewMessage(
            pattern=re.compile(r"(?i)\b(hitler|f[uü]hrer|(14)?88|HH)\b").search,
            outgoing=False))
@cooldown(60)
async def mein_fuhrer(event):
    blacklist = storage.blacklist or set()
    if event.chat_id in blacklist:
        return

    await event.reply(file=choice(responses))

@borg.on(borg.blacklist_plugin())
async def on_blacklist(event):
    storage.blacklist = await blacklist(event, storage.blacklist)
