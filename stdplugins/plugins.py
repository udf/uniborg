# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""
Show all loaded .plugins
"""
from telethon import events


@borg.on(events.NewMessage(pattern=r"\.plugins", outgoing=True))
async def _(event):
    result = f'{len(borg._plugins)} plugins loaded:'
    for name, mod in sorted(borg._plugins.items(), key=lambda t: t[0]):
        desc = (mod.__doc__ or '__no description__').replace('\n', ' ').strip()
        result += f'\n**{name}**: {desc}'

    await event.edit(result)
