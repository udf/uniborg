"""
This is a bot for silly replies.  See /help for a list of commands.
"""

@borg.on(borg.cmd(r"start$"))
async def start(event):
    if event.is_private:
        await event.respond(__doc__)
