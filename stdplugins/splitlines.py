# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""
.slines to split a multiline message into single line messages
"""

@borg.on(borg.cmd(r"slines", r"(?sm)(?:\s+(?P<args>.*))"))
async def _(event):
    await event.delete()
    for line in event.pattern_match["args"].splitlines():
        await event.respond(line)
