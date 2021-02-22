r"""Convert Weight

Convert weights to other common weights. 
Plugin gets triggered by a standalone message in the form of `{number} {weight1} in/to {weight2}`

Use /weights to list accepted weight units.

patterns: 
`(?i)^(\d+(?:(?:\.|,)\d+)?)? ?(k?g|ton(?:ne)?s?|lbs|oz|st(?:one)?) (?:to|in) (k?g|ton(?:ne)?s?|lbs|oz|st(?:one)?)$`
`/weights`
"""

from telethon import events
from uniborg.util import cooldown, edit_blacklist


units = {
    "g": 1,
    "kg": 1000,
    "tonne": 1000000,
    "lbs": 453.59237,
    "oz": 28.349523125,
    "st": 6350.29318,
    "stone": 6350.29318,
    "ton": 1016046.9088
}

async def is_plural(unit):
    if "ton" not in unit or not unit.endswith("s"):
        return unit

    return unit[:-1]

@borg.on(events.NewMessage(
    pattern=r"(?i)^(\d+(?:[\.,]\d+)?)? ?(k?g|ton(?:ne)?s?|lbs|oz|st(?:one)?) (?:to|in) (k?g|ton(?:ne)?s?|lbs|oz|st(?:one)?)$"
))
async def weight(event):
    blacklist = storage.blacklist or set()
    if event.chat_id in blacklist:
        return

    m = event.pattern_match
    value = m.group(1)

    if not value:
        value = 1
    value = value.replace(",", ".")

    unitfrom = await is_plural(m.group(2).lower())
    unitto = await is_plural(m.group(3).lower())

    result = round(float(value)*units[unitfrom]/units[unitto], 3)
    await event.reply(f"**{value} {unitfrom} is:**  `{result} {unitto}`")


@borg.on(borg.cmd(r"weights$"))
@cooldown(60)
async def list_weights(event):
    blacklist = storage.blacklist or set()
    if event.chat_id in blacklist:
        return

    text = f"**List of supported weights:**\n" + ", ".join(sorted(units.keys()))
    await event.reply(text)

@borg.on(borg.admin_cmd(r"(r)?blacklist", r"(?P<shortname>\w+)"))
async def blacklist_caller(event):
    storage.blacklist = await blacklist(event, storage.blacklist)
