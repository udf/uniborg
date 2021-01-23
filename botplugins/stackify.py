r"""Converts Minecraft blocks to stacks, stacks to blocks, and stacks and blocks to shulker boxes.
Examples:
• 635 blocks
• 635 blocks in/as stacks
• 9 stacks and 59 blocks
• 10 stacks
• 10 stacks in/as blocks
• 100 stacks in shulkers
• 100 blocks in shulker boxes


Add `s16` to the end to change the maximum stack size to 16 for items such as snowballs.

patterns:
• `(?i)(\d{1,9})(?: blocks(?: (?:in|as) stacks)?)(?: s(16|64))?$`
• `(?i)(\d{1,9})(?: stacks(?: (?:\+|and)( \d\d?)(?: blocks)?)?(?: (?:in|as) blocks)?)(?: s(16|64))?$`
• `(?i)(\d{1,9})(?: (blocks|stacks)(?: (?:in|as) shulker(?: ?boxe)?s))(?: s(16|64))?$`
"""

from telethon import events
from uniborg.util import cooldown


def plural(number, stupid_plural=False):
    if number == 1:
        return ""
    elif number != 1 and stupid_plural:
        return "es"
    else:
        return "s"


# Convert blocks to stacks
@borg.on(events.NewMessage(
    pattern=r"(?i)(\d{1,9})(?: blocks(?: (?:in|as) stacks)?)(?: s(16|64))?$",
    forwards=False)
)
async def stackify(event):
    """First calcuate how many full stacks, then the remainder."""

    m = event.pattern_match

    blocks = int(m.group(1))
    one_stack = int(m.group(2)) if m.group(2) else 64

    stacks = int(blocks / one_stack)
    remainder = blocks % one_stack

    total = f"**{blocks} block{plural(blocks)} is:** \
            \n`{stacks} stack{plural(stacks)} and {remainder} block{plural(remainder)}`"

    await event.reply(total)


#Convert stacks to blocks
@borg.on(events.NewMessage(
    pattern=r"(?i)(\d{1,9})(?: stacks(?: (?:\+|and)( \d\d?)(?: blocks)?)?(?: (?:in|as) blocks)?)(?: s(16|64))?$",
    forwards=False)
)
async def blockify(event):
    m = event.pattern_match

    stacks = int(m.group(1))
    remainder = int(m.group(2)) if m.group(2) else 0
    one_stack = int(m.group(3)) if m.group(3) else 64

    blocks = int(stacks * one_stack) + remainder
    if remainder:
        remainder_text = f" and {remainder} blocks"
    else:
        remainder_text = ""

    total = f"**{stacks} stack{plural(stacks)}{remainder_text} is:** \
            \n`{blocks} block{plural(blocks)}`"

    await event.reply(total)


# Convert blocks or stacks to shulkers
@borg.on(events.NewMessage(
    pattern=r"(?i)(\d{1,9})(?: (blocks|stacks)(?: (?:in|as) shulker(?: ?boxe)?s))(?: s(16|64))?$",
    forwards=False)
)
async def shulkerify(event):
    m = event.pattern_match

    amount = int(m.group(1))
    unit_type = m.group(2)
    one_stack = int(m.group(3)) if m.group(3) else 64

    stacks = amount
    amount_remainder = False
    if unit_type == "blocks":
        stacks = int(amount / one_stack)
        amount_remainder = amount % one_stack

    shulkers = int(stacks / 27)
    remainder = stacks % 27

    reply_msg = f"**{amount} {unit_type} is:** \
        \n`{shulkers} shulker box{plural(shulkers, True)}"

    if remainder:
        reply_msg += f", {remainder} stack{plural(remainder)}"
    if amount_remainder:
        reply_msg += f", {amount_remainder} block{plural(amount_remainder)}"

    # replace the last comma with ", and"
    reply_msg = ", and".join(reply_msg.rsplit(",", 1))

    await event.reply(reply_msg + "`")
