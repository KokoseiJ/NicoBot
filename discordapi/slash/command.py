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
from ..embed import Embed
from ..member import Member
from ..message import Message
from ..const import LIB_NAME, EMPTY
from ..dictobject import DictObject
from ..gateway import DiscordGateway
from ..util import get_formdata, clear_postdata

import json
import logging
from types import GeneratorType

__all__ = [
    "Context",
    "Option",
    "SubCommand",
    "SubCommandGroup",
    "String",
    "Integer",
    "Boolean",
    "UserOption",
    "ChannelOption",
    "RoleOption",
    "Mentionable",
    "Number",
    "SlashCommand",
    "SlashCommandManager"
]

CTX_KEYLIST = [
    "id",
    "application_id",
    "type",
    "data",
    "guild_id",
    "channel_id",
    "member",
    "user",
    "token",
    "version",
    "message",
]

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
    args = func.__code__.co_varnames[:func.__code__.co_argcount]
    if args[0] == "self":
        args = args[1:]
    return args


class Option:
    def __init__(self, type_, name, desc, choices, required, opts=None):
        self.type = type_
        self.name = name
        self.desc = desc
        self.choices = choices
        self.required = required
        self.options = opts

    def _json(self):
        data = {
            "type": self.type,
            "name": self.name,
            "description": self.desc,
        }

        if self.choices is not None:
            data.update({"choices": self.choices})
        if self.required is not None:
            data.update({"required": self.required})
        if self.options is not None:
            data.update({"options": self.options})

        return data

    @classmethod
    def from_command(cls, cmd):
        if isinstance(cmd, SubCommand):
            type_ = SUB_COMMAND_GROUP
        else:
            type_ = SUB_COMMAND
        options = [option._json() for option in cmd.options.values()]
        return cls(type_, cmd.name, cmd.desc, None, None, options)


class String(Option):
    def __init__(self, name, desc, choices=None, required=False):
        super().__init__(STRING, name, desc, choices, required)


class Integer(Option):
    def __init__(self, name, desc, choices=None, required=False):
        super().__init__(INTEGER, name, desc, choices, required)


class Boolean(Option):
    def __init__(self, name, desc, required=False):
        super().__init__(BOOLEAN, name, desc, None, required)


class UserOption(Option):
    def __init__(self, name, desc, required=False):
        super().__init__(USER, name, desc, None, required)


class ChannelOption(Option):
    def __init__(self, name, desc, required=False):
        super().__init__(CHANNEL, name, desc, None, required)


class RoleOption(Option):
    def __init__(self, name, desc, required=False):
        super().__init__(ROLE, name, desc, None, required)


class Mentionable(Option):
    def __init__(self, name, desc, required=False):
        super().__init__(MENTIONABLE, name, desc, None, required)


class Number(Option):
    def __init__(self, name, desc, choices=None, required=False):
        super().__init__(NUMBER, name, desc, choices, required)


class SlashCommand:
    def __init__(
            self,
            func,
            name,
            desc,
            options=[],
            default_permission=True,
            argcheck=True
    ):
        self.name = name
        self.desc = desc
        self.func = func
        self.default_permission = default_permission
        self.options = {option.name: option for option in options}

        func_args = get_func_args(func)

        if argcheck:
            for option in self.options.values():
                if not isinstance(option, Option):
                    raise ValueError(
                        "option should be Option, " f"not '{type(option)}'"
                    )

                if option.name not in func_args:
                    raise ValueError(
                        f"Argument '{option.name}' not present in "
                        f"function '{func.__code__.co_name}'"
                    )

    @classmethod
    def create(cls, desc, options=[], default_permission=True, cmdname=None):
        def decorator(func):
            if cmdname is None:
                name = func.__code__.co_name
            else:
                name = cmdname

            return cls(func, name, desc, options, default_permission)

        return decorator

    def execute(self, ctx, options, manager):
        logger.debug(options)
        logger.debug(ctx.token)

        ctx.manager = manager

        kwargs = {option: None for option in self.options}

        if options is None:
            options = []

        for option in options:
            name = option.get("name")
            value = option.get("options")
            
            if value is None:
                value = option.get("value")

            kwargs[name] = value

        func_self = getattr(self.func, "__self__", None)
        if func_self:
            kwargs.update({"self": func_self})

        gen = self.func(ctx=ctx, **kwargs)

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
            "default_permission": self.default_permission,
        }

        return data


class SubCommand(SlashCommand):
    def __init__(self, name, desc, *commands, default_permission=True):
        options = [Option.from_command(cmd) for cmd in commands]
        super().__init__(
            self.run, name, desc, options, default_permission, False)

        if isinstance(commands[0], list) or isinstance(commands[0], tuple):
            commands = commands[0]

        self.commands = {command.name: command for command in commands}

    def run(self, ctx, **kwargs):
        name, options = [(x, y) for x, y in kwargs.items() if y is not None][0]
        command = self.commands[name]
        return command.execute(ctx, options, ctx.manager)


class SubCommandGroup(SubCommand):
    pass


class SlashCommandManager:
    def __init__(self, client=None):
        self.client = None
        self.map = dict()

        if client is not None:
            self._set_client(client)

    def _set_client(self, client):
        if not isinstance(client, DiscordGateway):
            raise TypeError(
                "client should be DiscordGateway, not " f"'{type(client)}'"
            )
        self.client = client

    def register(self, *commands):
        for command in commands:
            if not isinstance(command, SlashCommand):
                raise TypeError(
                    "command should be SlashCommand, not " f"'{type(command)}'"
                )

            logger.info("Registering %s", command.name)

            self.map.update({command.name: command})

    def update(self):
        prev_raw = self.client.get_global_commands()
        prev = {cmd["name"]: cmd["id"] for cmd in prev_raw}

        for cmd in prev:
            if cmd not in self.map:
                self.client.delete_global_command(prev[cmd])

        commands = [command._json() for command in self.map.values()]
        self.client.bulk_global_commands(json.dumps(commands))

    def execute(self, ctx):
        cmdname = ctx.data["name"]
        logger.info(f"Executing command '{cmdname}'")

        command = self.map.get(cmdname)
        if command is None:
            logger.warning(f"Command '{cmdname}' not found")
            return

        gen = command.execute(ctx, ctx.data.get("options"), self)

        self.respond(ctx, 5)

        # TODO: Add the option to modify post-processor(res manipulation)

        for res in gen:
            if not res:
                self.delete(ctx)
                break
            if not isinstance(res, dict):
                if isinstance(res, Embed):
                    res = {"embeds": [res]}
                else:
                    res = {"content": res}
            self.edit(ctx, **res)

    def respond(self, ctx, type_, message=None):
        postdata = {"type": type_}
        if message is not None:
            postdata.update({"data": message})

        self.client.send_request(
            "POST", f"/interactions/{ctx.id}/{ctx.token}/callback", postdata
        )

    def edit(
        self,
        ctx,
        content=EMPTY,
        file=None,
        embeds=EMPTY,
        allowed_mentions=EMPTY,
        components=EMPTY,
    ):

        postdata = {
            "content": content,
            "embeds": embeds,
            "allowed_mentions": allowed_mentions,
            "components": components,
        }
        postdata = clear_postdata(postdata)

        if file is not None:
            if not isinstance(file, File):
                raise ValueError(f"file should be File, not {type(file)}")

            content_type, formdata = get_formdata(
                {"file": file, "payload_json": postdata}
            )

            headers = {"Content-Type": content_type}

            message = self.client.send_request(
                "PATCH",
                f"/webhooks/{self.client.user.id}/{ctx.token}"
                "/messages/@original",
                formdata,
                headers=headers,
            )
        else:
            message = self.client.send_request(
                "PATCH",
                f"/webhooks/{self.client.user.id}/{ctx.token}"
                "/messages/@original",
                postdata,
            )

        return Message(self.client, message)

    def delete(self, ctx):
        self.client.send_request(
            "DELETE",
            f"/webhooks/{self.client.user.id}/{ctx.token}/messages/@original",
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
