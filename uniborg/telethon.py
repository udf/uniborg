# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import asyncio
import logging

from telethon import TelegramClient
import telethon.utils

class Uniborg(TelegramClient):
    def __init__(self, session, **kwargs):
        self.logger = logging.getLogger(session)

        super().__init__(session,
                17349, "344583e45741c457fe1862106095a5eb", # yarr
                **kwargs)

        asyncio.get_event_loop().run_until_complete(self.async_init())

    async def async_init(self):
        await self.start()

        self.uid = telethon.utils.get_peer_id(await self.get_me())

    def run(self):
        asyncio.get_event_loop().run_forever()
