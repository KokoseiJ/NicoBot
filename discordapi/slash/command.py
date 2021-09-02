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

from ..user import User
from ..member import Member
from ..const import LIB_NAME
from ..message import Message
from ..dictobject import DictObject
from ..gateway import DiscordGateway

import json
import logging

__all__ = ["Context", "Option", "SubCommand", "SubCommandGroup", "String",
           "Integer", "Boolean", "UserOption", "ChannelOption", "RoleOption",
           "Mentionable", "Number", "SlashCommand"]

CTX_KEYLIST = ["id", "application_id", "type", "data", "guild_id",
               "channel_id", "member", "user", "token", "version", "message"]

SUB_COMMAND = 1
SUB_COMMAND_GROUP = 2
STRING = 3
INTEGER = 4
BOOLEAN = 5
USER = 6
CHANNEL = 7
ROLE = 8
MENTIONABLE = 9
NUMBER = 10

logger = logging.getLogger(LIB_NAME)


def get_func_args(func):
    return func.__code__.co_varnames[:func.__code__.co_argcount]


class Option:
    def __init__(self, type_, name, desc, choices, cmd, subcmds, required):
        self.type = type_
        self.name = name
        self.desc = desc
        self.choices = choices
        self.cmd = cmd
        self.subcmds = subcmds
        self.required = required

        if subcmds is not None:
            for cmd in subcmds:
                if not isinstance(cmd, SlashCommand):
                    raise ValueError("Subcommand should be SlashCommand, "
                                     f"not '{type(cmd)}'")

    def _json(self):
        data = {
            "type": self.type,
            "name": self.name,
            "description": self.desc,
            "required": self.required
        }

        if self.choices is not None:
            data.update({"choices": self.choices})

        if self.cmd is not None:
            options = self.cmd.options
            data.update({"options": options})
        
        elif self.subcmds is not None:
            options = [cmd._json() for cmd in self.subcmds]
            data.update({"options": options})

        return data


class SubCommand(Option):
    def __init__(self, cmd, name=None, desc=None, required=False):
        super().__init__(SUB_COMMAND, name, desc, None, cmd, None, required)


class SubCommandGroup(Option):
    def __init__(self, name, desc, subcmds, required=False):
        super().__init__(
            SUB_COMMAND_GROUP, name, desc, None, None, subcmds, required)


class String(Option):
    def __init__(self, name, desc, choices=None, required=False):
        super().__init__(STRING, name, desc, choices, None, None, required)


class Integer(Option):
    def __init__(self, name, desc, choices=None, required=False):
        super().__init__(INTEGER, name, desc, choices, None, None, required)


class Boolean(Option):
    def __init__(self, name, desc, required=False):
        super().__init__(BOOLEAN, name, desc, None, None, None, required)


class UserOption(Option):
    def __init__(self, name, desc, required=False):
        super().__init__(USER, name, desc, None, None, None, required)


class ChannelOption(Option):
    def __init__(self, name, desc, required=False):
        super().__init__(CHANNEL, name, desc, None, None, None, required)


class RoleOption(Option):
    def __init__(self, name, desc, required=False):
        super().__init__(ROLE, name, desc, None, None, None, required)


class Mentionable(Option):
    def __init__(self, name, desc, required=False):
        super().__init__(MENTIONABLE, name, desc, None, None, None, required)


class Number(Option):
    def __init__(self, name, desc, choices=None, required=False):
        super().__init__(NUMBER, name, desc, choices, None, None, required)


class SlashCommand:
    def __init__(self, name, desc, func, options):
        self.name = name
        self.desc = desc
        self.func = func
        self.options = {option.name: option for option in options}

        func_args = get_func_args(func)

        for option in self.options.values():
            if not isinstance(option, Option):
                raise ValueError("option should be Option, "
                                 f"not '{type(option)}'")

            if option.name not in func_args:
                raise ValueError(f"Argument '{option.name}' not present in "
                                 f"function '{func.__code__.co_name}'")

    @classmethod
    def create(cls, desc, options):
        def decorator(func):
            name = func.__code__.co_name
            return cls(name, desc, func, options)
        return decorator

    def execute(self, ctx, options):
        logger.info(options)
        logger.info(ctx.data)

    def _json(self):
        data = {
            "type": 1,
            "name": self.name,
            "description": self.desc,
            "options": [option._json() for option in self.options.values()]
        }

        return data


class SlashCommandManager:
    def __init__(self, client=None):
        self.client = None
        self.map = dict()

        self._set_client(client)

    def _set_client(self, client):
        if not isinstance(client, DiscordGateway):
            raise TypeError("client should be DiscordGateway, not "
                            f"'{type(client)}'")
        self.client = client

    def register(self, command):
        if not isinstance(command, SlashCommand):
            raise TypeError("command should be SlashCommand, not "
                            f"'{type(command)}'")

        self.map.update({command.name: command})

    def update(self):
        commands = [command._json() for command in self.map.values()]
        self.client.bulk_global_commands(json.dumps(commands))

    def execute(self, ctx):
        cmdname = ctx.data['name']
        command = self.map.get(cmdname)
        if command is None:
            logger.warning(f"Command '{cmdname}' not found")
            return

        command.execute(ctx, ctx.data['options'])


class Context(DictObject):
    def __init__(self, client, data):
        super().__init__(data, CTX_KEYLIST)
        self.client = client

        if self.user is not None:
            self.user = User(client, self.user)
        if self.member is not None:
            self.member = Member(client, self.member)
        if self.message is not None:
            self.message = Message(client, self.message)
