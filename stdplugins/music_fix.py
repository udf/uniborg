# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""
Auto-fix audio files sent as voice-notes
"""
from telethon import events

@borg.on(events.NewMessage(outgoing=True))
async def _(e):
    if e.fwd_from or e.via_bot_id:
        return

    if e.voice:
        f = e.file
        if f.title and f.performer:
            caption = f"{f.performer} - {f.title}"
        elif f.title:
            caption = f.title
        elif f.name:
            caption = f.name
        else:
            caption = None

        if caption:
            await e.edit(caption)
