# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""
Turn YouTube Shorts links into regular video links
"""

from telethon import events

@borg.on(events.NewMessage(outgoing=True,
    pattern=r"^https://youtube\.com/shorts/([\w-]{11})\?feature=share"))
async def _(event):
    video_id = event.pattern_match.group(1)
    await event.edit(f"https://www.youtube.com/watch?v={video_id}",
            link_preview=True)
