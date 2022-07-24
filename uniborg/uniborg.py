# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import asyncio
import importlib.util
import inspect
import logging
from pathlib import Path

from telethon import TelegramClient
import telethon.utils
import telethon.events

from .storage import Storage
from . import hacks
from . import util


class Uniborg(TelegramClient):
    def __init__(
            self, session, *, plugin_path="plugins", storage=None, admins=[],
            bot_token=None, **kwargs):
        # TODO: handle non-string session
        #
        # storage should be a callable accepting plugin name -> Storage object.
        # This means that using the Storage type as a storage would work too.
        self._name = session
        self.storage = storage or (lambda n: Storage(Path("data") / n))
        self._logger = logging.getLogger(session)
        self._plugins = {}
        self._plugin_path = plugin_path
        self.admins = admins

        kwargs = {
            "api_id": 6, "api_hash": "eb06d4abfb49dc3eeb1aeb98ae0f581e",
            **kwargs}
        super().__init__(session, **kwargs)

        # This is a hack, please avert your eyes
        # We want this in order for the most recently added handler to take
        # precedence
        self._event_builders = hacks.ReverseList()

        self.loop.run_until_complete(self._async_init(bot_token=bot_token))

    async def _async_init(self, **kwargs):
        await self.start(**kwargs)

        self.me = await self.get_me()
        self.uid = telethon.utils.get_peer_id(self.me)

        core_plugin = Path(__file__).parent / "_core.py"
        await self.load_plugin_from_file(core_plugin)

        for p in Path().glob(f"{self._plugin_path}/*.py"):
            await self.load_plugin_from_file(p)

    async def load_plugin(self, shortname):
        await self.load_plugin_from_file(f"{self._plugin_path}/{shortname}.py")

    async def load_plugin_from_file(self, path):
        path = Path(path)
        shortname = path.stem
        name = f"_UniborgPlugins.{self._name}.{shortname}"

        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)

        mod.borg = self
        mod.logger = logging.getLogger(shortname)
        mod.storage = self.storage(f"{self._name}/{shortname}")

        try:
            spec.loader.exec_module(mod)
        except util.StopImport:
            return
        self._plugins[shortname] = mod

        if callable(getattr(mod, 'load', None)):
            try:
                unload = mod.unload()
                if inspect.isawaitable(unload):
                    await unload
            except Exception:
                self._logger.exception(f'Unhandled exception loading {shortname}')

        self._logger.info(f"Successfully loaded plugin {shortname}")

    async def remove_plugin(self, shortname):
        name = self._plugins[shortname].__name__

        for i in reversed(range(len(self._event_builders))):
            ev, cb = self._event_builders[i]
            if cb.__module__ == name:
                del self._event_builders[i]

        plugin = self._plugins.pop(shortname)
        if callable(getattr(plugin, 'unload', None)):
            try:
                unload = plugin.unload()
                if inspect.isawaitable(unload):
                    await unload
            except Exception:
                self._logger.exception(f'Unhandled exception unloading {shortname}')

        del plugin
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

    def cmd(self, command, pattern=None, admin_only=False):
        command = fr'(?:{command})'
        if self.me.bot:
            command = fr'{command}(?:@{self.me.username})?'

        if pattern is not None:
            pattern = fr'{command}{pattern}'
        else:
            pattern = command

        if not self.me.bot:
            pattern=fr'^\.{pattern}'
        else:
            pattern=fr'^\/{pattern}'
        pattern=fr'(?i){pattern}$'

        if self.me.bot and admin_only:
            allowed_users = self.admins
        else:
            allowed_users = None

        return telethon.events.NewMessage(
            outgoing=not self.me.bot,
            from_users=allowed_users,
            pattern=pattern
        )

    def admin_cmd(self, command, pattern=None):
        return self.cmd(command, pattern, admin_only=True)
