#
# NicoBot is Nicovideo Player bot for Discord, written from the scratch.
# This file is part of NicoBot.
#
# Copyright (C) 2021 Wonjun Jung (KokoseiJ)
#
#    Nicobot is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#

from .gateway import DiscordGateway
from .handler import MethodEventHandler, ThreadedMethodEventHandler
from types import GeneratorType

__all__ = ["CommandError", "CommandManager", "CommandEventHandler",
           "ThreadedCommandEventHandler"]


class CommandError(Exception):
    def __init__(self, command, title, message):
        self.command = command
        self.title = title
        self.message = message


class CommandManager:
    def __init__(self, client=None):
        self.client = None

        if client is not None:
            self._set_client(client)

    def _set_client(self, client):
        if not isinstance(client, DiscordGateway):
            raise TypeError("client should be DiscordGateway, "
                            f"not {type(client)}")
        self.client = client

    def execute_cmd(self, cmdinput, message):
        cmdsplit = cmdinput.split(" ", 1)
        cmd = cmdsplit[0].lower()
        if len(cmdsplit) == 2:
            args = cmdsplit[1]
        else:
            args = ""

        handler = getattr(self, cmd, None)
        gen = handler(args, message)
        
        if isinstance(gen, GeneratorType):
            for x in gen:
                yield x
        else:
            yield gen


class CommandEventHandler(MethodEventHandler):
    def __init__(self, manager, prefix):
        self.manager = None
        self.prefix = prefix

        self._set_manager(manager)

    def _set_manager(self, manager):
        if isinstance(manager, CommandManager):
            self.manager = manager
        elif issubclass(manager, CommandManager):
            self.manager = manager()
        else:
            raise TypeError("manager should be CommandManager, "
                            f"not {type(manager)}")

    def on_message_create(self, message):
        if not message.content.startswith(self.prefix) or message.author.bot:
            return
        msg = message.content[len(self.prefix):]

        try:
            gen = self.manager.execute_cmd(msg, message)
            # title = msg.split(" ", 1)[0]
            for content in gen:
                message.channel.send(content=content)
        except CommandError as e:
            # title = e.title
            content = e.message
            message.channel.send(content=content)


class ThreadedCommandEventHandler(
        CommandEventHandler, ThreadedMethodEventHandler):
    pass
