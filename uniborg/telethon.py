# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import asyncio
import importlib.util
import logging
from pathlib import Path

from telethon import TelegramClient
import telethon.utils
import telethon.events

from . import hacks


class Uniborg(TelegramClient):
    def __init__(
            self, session, *, plugin_path="plugins",
            bot_token=None, **kwargs):
        # TODO: handle non-string session
        self._name = session
        self._logger = logging.getLogger(session)
        self._plugins = {}
        self._plugin_path = plugin_path

        super().__init__(
                session,
                17349, "344583e45741c457fe1862106095a5eb",  # yarr
                **kwargs)

        # This is a hack, please avert your eyes
        # We want this in order for the most recently added handler to take
        # precedence
        self._event_builders = hacks.ReverseList()

        self._loop.run_until_complete(self._async_init(bot_token=bot_token))

        core_plugin = Path(__file__).parent / "_core.py"
        self.load_plugin_from_file(core_plugin)

        for p in Path().glob(f"{self._plugin_path}/*.py"):
            self.load_plugin_from_file(p)

    async def _async_init(self, **kwargs):
        await self.start(**kwargs)

        self.me = await self.get_me()
        self.uid = telethon.utils.get_peer_id(self.me)

    def run(self):
        self._loop.run_forever()

    def load_plugin(self, shortname):
        self.load_plugin_from_file(f"{self._plugin_path}/{shortname}.py")

    def load_plugin_from_file(self, path):
        path = Path(path)
        shortname = path.stem
        name = f"_UniborgPlugins.{self._name}.{shortname}"

        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)

        mod.borg = self
        mod.logger = logging.getLogger(shortname)

        spec.loader.exec_module(mod)
        self._plugins[shortname] = mod
        self._logger.info(f"Successfully loaded plugin {shortname}")

    def remove_plugin(self, shortname):
        name = self._plugins[shortname].__name__

        i = len(self._event_builders)
        while i:
            i -= 1
            ev, cb = self._event_builders[i]
            if cb.__module__ == name:
                del self._event_builders[i]

        del self._plugins[shortname]
        self._logger.info(f"Removed plugin {shortname}")

    def await_event(self, event_matcher, filter=None):
        fut = asyncio.Future()

        @self.on(event_matcher)
        async def cb(event):
            try:
                if filter is None or await filter(event):
                    fut.set_result(event)
            except telethon.events.StopPropagation:
                fut.set_result(event)
                raise

        fut.add_done_callback(
                lambda _: self.remove_event_handler(cb, event_matcher))

        return fut
