r"""Convert distances to other common distances. 
Plugin gets triggered by a standalone message in the form of `{number} {distance1} in/to {distance2}`

Use /distances to list accepted weight units.

patterns: 
`(?i)(\d+(?:(?:\.|,)\d+)?)? ?((?:[ckm]?m(?:et(?:er|re)s?)?|inch(?:es)?|f[oe]+t|(?:banana|yard|mile|parsec)s?|au|ly)) (?:to|in) ((?:[ckm]?m(?:et(?:er|re)s?)?|inch(?:es)?|f[oe]+t|(?:banana|yard|mile|parsec)s?|au|ly))$$`
`/distances`
"""

from telethon import events
from uniborg.util import cooldown


units = {
    "mm": 0.001,
    "cm": 0.01,
    "inch": 0.0254,
    "banana": 0.17799,
    "foot": 0.3048,
    "m": 1,
    "yard": 1.0936132983,
    "km": 1000,
    "mile": 1609.344,
    "au": 149597900000,
    "ly": 9460730000000000,
    "parsec": 30856780000000000,
}


def singular(unit):
    if len(unit) < 3:
        return unit
    if "inch" in unit:
        return "inch"
    if "met" in unit:
        return "m"
    if unit.endswith("s"):
        return unit[:-1]
    if "feet" in unit:
        return "foot"

    return unit


def plural(unit, amount):
    if amount == 1:
        return unit
    if len(unit) < 3:
        return unit
    if unit not in ["foot", "inch"]:
        return unit + "s"
    if "foot" in unit:
        return "feet"
    if "inch" in unit:
        return "inches"

    return unit


@borg.on(events.NewMessage(
    pattern=r"(?i)(\d+(?:[\.,]\d+)?)? ?((?:[ckm]?m(?:et(?:er|re)s?)?|inch(?:es)?|f[oe]+t|(?:banana|yard|mile|parsec)s?|au|ly)) (?:to|in) ((?:[ckm]?m(?:et(?:er|re)s?)?|inch(?:es)?|f[oe]+t|(?:banana|yard|mile|parsec)s?|au|ly))$"
))
async def distance(event):
    m = event.pattern_match
    value = m.group(1)

    if not value:
        value = 1
    value = value.replace(",", ".")

    unitfrom = singular(m.group(2).lower())
    unitto = singular(m.group(3).lower())

    try:
        result = round(float(value)*units[unitfrom]/units[unitto], 3)
    except ValueError:
        pass

    plural_from = plural(unitfrom, float(value))
    plural_to = plural(unitto, result)

    await event.reply(f"**{value} {plural_from} is:**  `{result} {plural_to}`")


@borg.on(borg.cmd(r"distances$"))
@cooldown(60)
async def list_distances(event):
    text = f"**List of supported distance units:**\n" + ", ".join(sorted(units.keys()))
    await event.reply(text)
