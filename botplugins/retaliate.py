"""If you say "love you botname/username" the bot will respond with "love you too!"
It also works with other words, like "fuck", "screw", "damn"

Limits to once every 30 seconds.

patterns:  
`(?i)((i ?)?l(ove)?( ?(y|(yo)?u))) @?({fname}|{name}|{username})`

`(?i)((fuck|screw|damn?) (yo)?u) @?({fname}|{name}|{username})`
"""

import re
from telethon import events
from uniborg.util import cooldown, edit_blacklist


# love and hate
@borg.on(events.NewMessage(
    pattern=re.compile(r"(?i)((?:i ?)?l(?:o+ve )?(?:y(?:ou)?|u))").search, forwards=False))
@borg.on(events.NewMessage(
    pattern=re.compile(r"(?i)((?:i hate|fuck|screw|damn?) (?:yo)?u)").search, forwards=False))
@borg.on(events.NewMessage(
    pattern=re.compile(r"(?i)(thank(?:s| you|u+)|ty)").search, forwards=False))
@cooldown(10)
async def retaliate(event):
    blacklist = storage.blacklist or set()
    if event.chat_id in blacklist:
        return

    me = await event.client.get_me()
    name = me.first_name
    fname = re.sub(r"\W.+", "", name)
    username = me.username
    match = event.pattern_match

    if not re.search(fr"(?i)({fname}|{name}|{username})", match.string):
        return
    if "thank" in match.string or re.search(r"(^ty|ty$)", match.string):
        await event.reply("You're welcome!")
        return

    await event.reply(f"{match.group(1)} too!")    # "Love you too!"


@borg.on(borg.admin_cmd(r"(r)?blacklist", r"(?P<shortname>\w+)"))
async def blacklist(event):
    m = event.pattern_match
    shortname = m["shortname"]

    if shortname not in __file__:
        return

    storage.blacklist = edit_blacklist(event.chat_id, storage.blacklist, m.group(1))
    await event.reply("Updated blacklist.")
