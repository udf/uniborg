"""Dice roll

Will roll a __x__ sided dice __n__ times.
Examples:
• `/roll 3d20`
• `/roll d6 2d7 3d8` (between 1 and 20 dice)

pattern: `/roll@bot_username? ((?:\d*d\d+\s*)+)$`
"""

import re
from random import randint
from uniborg.util import cooldown, edit_blacklist
from telethon import client, events, errors


@borg.on(borg.cmd(r"roll ((?:\d*d\d+\s*)+)$"))
@cooldown(10)
async def on_roll(event):
    blacklist = storage.blacklist or set()
    if event.chat_id in blacklist:
        return

    match = event.pattern_match.group(1)

    dice_pattern = r"(\d*)d(\d+)" # the pattern to apply to m.group(2)
    dice_match = re.finditer(dice_pattern, match)

    outputs = list()
    total = int()
    output_strings = list()

    roll_limit = 0
    for d in dice_match:
        if roll_limit == 20: # cap the amount of dice/roll pairs at 20
            break

        ## set the amount of rolls to 1 if n in nd6 is not specified
        rolls = 1
        if d.group(1):
            rolls = int(d.group(1))

        sides = int(d.group(2)) # how many "sides" the dice has

        ## limit the amount of rolls and sides
        if rolls > 500 or sides > 100000:
            await event.respond("The maximum rolls is 500, and the maximum amount of sides is 100,000.")
            return

        output_strings.append(f"**{rolls}d{sides}:**") # add the dice/roll pair to the output string

        ## quick maffs: sort each roll's result, and sum up all results
        val = list()
        for _ in range(0, rolls):
            r = randint(1, sides)
            val.append(str(r))
            total += r

        outputs.extend(val)
        output_strings.append(f"`{' '.join(val)}`") # add each result to the output string
        roll_limit += 1

    ## if there's more than one roll, reply with the total added to the end
    if len(outputs) > 1:
        output_strings.append(f"**=** `{total}`")

    output = "\n".join(output_strings)

    try:
        await event.respond(f"{output}")
    except errors.MessageTooLongError:
        await event.respond(f"**Total =** `{total}`\n"
                            + "Tip:  Message was too long, try rolling less dice next time")


@borg.on(borg.admin_cmd(r"(r)?blacklist", r"(?P<shortname>\w+)"))
async def blacklist(event):
    m = event.pattern_match
    shortname = m["shortname"]

    if shortname not in __file__:
        return

    storage.blacklist = edit_blacklist(event.chat_id, storage.blacklist, m.group(1))
    await event.reply("Updated blacklist.")
