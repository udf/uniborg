r"""Yes...  Or No?

Adding "yes or no" to the end of your message will result in a yes or no answer from the bot.
Also supports "y/n", and other alternatives.

Will also respond with an 8ball answer to `/8ball`

patterns:
`(?i)(yes|y)(/| or )(no|n)\??$`
`/8ball`
"""

import re
from random import choice
from telethon import events
from uniborg.util import edit_blacklist


answers = [
    "As I see it, yes.",
    "Ask again later.",
    "Better not tell you now.",
    "Cannot predict now.",
    "Concentrate and ask again.",
    "Don't count on it.",
    "It is certain.",
    "It is decidedly so.",
    "Most likely.",
    "My reply is no.",
    "My sources say no.",
    "No.",
    "No - don't even think about it.",
    "Outlook good.",
    "Outlook not so good.",
    "Reply hazy, try again.",
    "Signs point to yes.",
    "Very doubtful.",
    "Very unlikely.",
    "Without a doubt.",
    "Yes.",
    "Yes - definitely.",
    "You may rely on it.",
]


# Yes or no
# Matches "y/n" "yes or no" "yes/no?" etc
@borg.on(events.NewMessage(
    pattern=re.compile(r"(?i)(yes|y)(/| or )(no|n)\??$").search, forwards=False))
@borg.on(borg.cmd(r"8ball( .+)?"))
async def yes_or_no(event):
    blacklist = storage.blacklist or set()
    if event.chat_id in blacklist:
        return

    print(event.pattern_match.string)
    if not (event.pattern_match.string).startswith("/8ball"):
        await event.reply(choice(("Yes.", "No.")))
        return

    await event.reply(choice(answers))


@borg.on(borg.admin_cmd(r"(r)?blacklist", r"(?P<shortname>\w+)"))
async def blacklist(event):
    m = event.pattern_match
    shortname = m["shortname"]

    if shortname not in __file__:
        return

    storage.blacklist = edit_blacklist(event.chat_id, storage.blacklist, m.group(1))
    await event.reply("Updated blacklist.")
