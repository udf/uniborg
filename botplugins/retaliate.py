"""Retaliate

If you say "love you botname/username" the bot will respond with "love you too!"
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
# @cooldown(10)
async def retaliate(event):
    blacklist = storage.blacklist or set()
    if event.chat_id in blacklist:
        return

    me = await event.client.get_me()
    name = me.first_name
    fname = re.sub(r"\W.+", "", name)
    username = me.username
    name_list = "|".join([name, fname, username])

    match = event.pattern_match
    string = match.string.replace("\\", u"\u005c\u005c")

    if not re.search(fr"(^{match.group(1)}\s|{match.group(1)}!?$)", string):
        return
    if not re.search(fr"(?i)(^({name_list})\s|({name_list})!?$)", string):
        return
    if "thank" in match.string or re.search(r"(^ty|ty$)", string):
        await event.reply("You're welcome!")
        return

    content = (match.group(1)).rstrip("!")
    await event.reply(f"{content} too!")    # "Love you too!"

@borg.on(borg.admin_cmd(r"(r)?blacklist", r"(?P<shortname>\w+)"))
async def blacklist_caller(event):
    storage.blacklist = await blacklist(event, storage.blacklist)
