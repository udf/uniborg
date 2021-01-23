r"""Adding "yes or no" to the end of your message will result in a yes or no answer from the bot.
Also supports "y/n", and other alternatives.

pattern:  `(?i)(yes|y)(/| or )(no|n)\??$`
"""

import re
from random import choice
from telethon import events


# Yes or no
# Matches "y/n" "yes or no" "yes/no?" etc
@borg.on(events.NewMessage(
    pattern=re.compile(r"(?i)(yes|y)(/| or )(no|n)\??$").search, forwards=False))
async def yes_or_no(event):
    await event.reply(choice(("Yes.", "No.")))
