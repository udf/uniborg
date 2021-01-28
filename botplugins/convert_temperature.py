"""Converts celsius to fahrenheit and back.  Example:
"5°C in degrees f"
Accepts variations of "°C", for example "c", "degrees Celsius", or "degrees C".
Case insensitive.

patterns:
`(?i)^(\d{1,9}|-\d{1,9})( ?° ?| degrees)? ?c(elsius)? (to|in) (°|degrees)?f(ahrenheit)?$`

`(?i)^(\d{1,9}|-\d{1,9})( ?° ?| degrees)? ?f(ahrenheit)? (to|in) (°|degrees)?c(elsius)?$`
"""

from telethon import events
from uniborg.util import edit_blacklist


#Convert Celsius to Fahrenheit
@borg.on(events.NewMessage(pattern=r"(?i)^(\d{1,9}|-\d{1,9})( ?° ?| degrees)? ?c(elsius)? (to|in) (°|degrees)?f(ahrenheit)?$"))
async def c_to_f(event):
    blacklist = storage.blacklist or set()
    if event.chat_id in blacklist:
        return

    c = int(event.pattern_match.group(1))
    sum = round((c * 1.8 + 32), 2)
    await event.reply(f"**{c} °C is:**  `{sum} °F`")


#Convert Fahrenheit to Celsius
@borg.on(events.NewMessage(pattern=r"(?i)^(\d{1,9}|-\d{1,9})( ?° ?| degrees)? ?f(ahrenheit)? (to|in) (°|degrees)?c(elsius)?$"))
async def f_to_c(event):
    blacklist = storage.blacklist or set()
    if event.chat_id in blacklist:
        return

    f = int(event.pattern_match.group(1))
    sum = round(((f - 32) * 0.55555555555), 2)
    await event.reply(f"**{f} °F is:**  `{sum} °C`")


@borg.on(borg.admin_cmd(r"(r)?blacklist", r"(?P<shortname>\w+)"))
async def blacklist(event):
    m = event.pattern_match
    shortname = m["shortname"]

    if shortname not in __file__:
        return

    storage.blacklist = edit_blacklist(event.chat_id, storage.blacklist, m.group(1))
    await event.reply("Updated blacklist.")
