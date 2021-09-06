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

from ..file import File
from ..user import User
from ..member import Member
from ..message import Message
from ..const import LIB_NAME, EMPTY
from ..dictobject import DictObject
from ..gateway import DiscordGateway
from ..util import get_formdata, clear_postdata

import json
import logging
from types import GeneratorType

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
            self.subcmds = {cmd.name: cmd for cmd in subcmds}

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
            options = [cmd._json() for cmd in self.subcmds.values()]
            data.update({"options": options})

        return data


class SubCommand(Option):
    def __init__(self, cmd, name=None, desc=None, required=False):
        super().__init__(SUB_COMMAND, name, desc, None, cmd, None, required)


class SubCommandGroup(Option):
    def __init__(self, name, desc, subcmds, required=False):
        super().__init__(
            SUB_COMMAND_GROUP, name, desc, None, None, subcmds, required)

    def execute(self, ctx, options, manager):
        if options:
            options = options[0]
        else:
            options = {}
        handler = self.subcmds[options.get('name')]
        if handler is not None:
            return handler.execute(ctx, options.get('options'), manager)


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
    def __init__(self, name, desc, func, options, default_permission):
        self.name = name
        self.desc = desc
        self.func = func
        self.options = {option.name: option for option in options}
        self.default_permission = default_permission

        func_args = get_func_args(func)

        for option in self.options.values():
            if not isinstance(option, Option):
                raise ValueError("option should be Option, "
                                 f"not '{type(option)}'")

            if option.name not in func_args:
                raise ValueError(f"Argument '{option.name}' not present in "
                                 f"function '{func.__code__.co_name}'")

    @classmethod
    def create(cls, desc, options, default_permission=True):
        def decorator(func):
            name = func.__code__.co_name
            return cls(name, desc, func, options, default_permission)
        return decorator

    def execute(self, ctx, options, manager):
        logger.info(options)
        logger.info(ctx.token)

        ctx.manager = manager

        kwargs = {option: None for option in self.options}

        if options is None:
            options = []

        for option in options:
            type_ = option.get('type')
            name = option.get('name')
            value = option.get('value')
            opts = option.get('options')
            if type_ == SUB_COMMAND:
                value = self.options[name].cmd.execute(ctx, opts, manager)
            elif type_ == SUB_COMMAND_GROUP:
                value = self.options[name].execute(ctx, opts, manager)

            kwargs[name] = value

        gen = self.func(ctx, **kwargs)

        if isinstance(gen, GeneratorType):
            for res in gen:
                yield res
        else:
            yield gen

    def _json(self):
        data = {
            "type": 1,
            "name": self.name,
            "description": self.desc,
            "options": [option._json() for option in self.options.values()],
            "default_permission": self.default_permission
        }

        return data


class SlashCommandManager:
    def __init__(self, client=None):
        self.client = None
        self.map = dict()

        if client is not None:
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
        prev_raw = self.client.get_global_commands()
        prev = {cmd['name']: cmd['id'] for cmd in prev_raw}

        for cmd in prev:
            if cmd not in self.map:
                self.client.delete_global_command(prev[cmd])

        commands = [command._json() for command in self.map.values()]
        self.client.bulk_global_commands(json.dumps(commands))

    def execute(self, ctx):
        cmdname = ctx.data['name']
        command = self.map.get(cmdname)
        if command is None:
            logger.warning(f"Command '{cmdname}' not found")
            return

        gen = command.execute(ctx, ctx.data.get('options'), self)

        self.respond(ctx, 5)

        for res in gen:
            if not res:
                self.delete(ctx)
                break
            self.edit(ctx, content=res)

    def respond(self, ctx, type_, message=None):
        postdata = {
            "type": type_
        }
        if message is not None:
            postdata.update({"data": message})

        self.client.send_request(
            "POST", f"/interactions/{ctx.id}/{ctx.token}/callback", postdata
        )

    def edit(self, ctx, content=EMPTY, file=None, embeds=EMPTY,
             allowed_mentions=EMPTY, components=EMPTY):
        
        postdata = {
            "content": content,
            "embeds": embeds,
            "allowed_mentions": allowed_mentions,
            "components": components
        }
        postdata = clear_postdata(postdata)

        if file is not None:
            if not isinstance(file, File):
                raise ValueError(f"file should be File, not {type(file)}")

            content_type, formdata = get_formdata({
                "file": file,
                "payload_json": postdata
            })

            headers = {"Content-Type": content_type}

            message = self.client.send_request(
                "PATCH",
                f"/webhooks/{self.client.user.id}/{ctx.token}"
                "/messages/@original",
                formdata, headers=headers
            )
        else:
            message = self.client.send_request(
                "PATCH",
                f"/webhooks/{self.client.user.id}/{ctx.token}"
                "/messages/@original",
                postdata
            )

        return Message(self.client, message)

    def delete(self, ctx):
        self.client.send_request(
            "DELETE",
            f"/webhooks/{self.client.user.id}/{ctx.token}/messages/@original"
        )


class Context(DictObject):
    def __init__(self, client, data):
        super().__init__(data, CTX_KEYLIST)
        self.client = client
        self.manager = None

        if self.user is not None:
            self.user = User(client, self.user)
        if self.member is not None and self.guild_id is not None:
            guild = client.get_guild(self.guild_id)
            self.member = Member(client, guild, self.member)
        if self.message is not None:
            self.message = Message(client, self.message)
