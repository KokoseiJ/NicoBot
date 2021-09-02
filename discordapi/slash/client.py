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

from ..gateway import GatewayEventParser
from ..handler import MethodEventHandler
from ..client import DiscordClient
from .command import Context, SlashCommandManager

__all__ = ["DiscordInteractionClient", "InteractionEventHandler",
           "InteractionEventParser"]


class DiscordInteractionClient(DiscordClient):
    def __init__(self, token, handler=None, event_parser=None,
                 command_manager=None, intents=32509, name="main"):
        if handler is None:
            handler = InteractionEventHandler
        if event_parser is None:
            event_parser = InteractionEventParser
        if command_manager is None:
            command_manager = SlashCommandManager
        super(DiscordInteractionClient, self).__init__(
            token=token,
            handler=handler,
            event_parser=event_parser,
            intents=intents,
            name=name)

        self.command_manager = command_manager(self)

    def __send_request(self, method, route, data=None, expected_code=None,
                       raise_at_exc=True, baseurl=None, headers=None):
        route = f"/applications/{self.user.id}{route}"
        return self.send_request(
            method, route, data, expected_code, raise_at_exc, baseurl, headers
        )

    def get_global_commands(self):
        commands = self.__send_request(
            "GET", "/commands"
        )

        return commands

    def create_global_command(self, command):
        command = self.__send_request(
            "POST", "/commands", command
        )

        return command

    def get_global_command(self, id_):
        command = self.__send_request(
            "GET", f"/commands/{id_}"
        )

        return command

    def edit_global_command(self, id_, command):
        command = self.__send_request(
            "PATCH", f"/commands/{id_}", command
        )

        return command

    def delete_global_command(self, id_):
        self.__send_request(
            "DELETE", f"/commands/{id_}"
        )

    def bulk_global_commands(self, commands):
        commands = self.__send_request(
            "PUT", "/commands", commands
        )

        return commands

    def get_guild_commands(self, guild):
        commands = self.__send_request(
            "GET", f"/guilds/{guild.id}/commands"
        )

        return commands

    def create_guild_command(self, guild, command):
        command = self.__send_request(
            "POST", f"/guilds/{guild.id}/commands", command
        )

        return command

    def get_guild_command(self, guild, id_):
        command = self.__send_request(
            "GET", f"/guilds/{guild.id}/commands/{id_}"
        )

        return command

    def edit_guild_command(self, guild, id_, command):
        command = self.__send_request(
            "PATCH", f"/guilds/{guild.id}/commands/{id_}", command
        )

        return command

    def delete_guild_command(self, guild, id_):
        self.__send_request(
            "DELETE", f"/guilds/{guild.id}/commands/{id_}"
        )

    def bulk_guild_commands(self, guild, commands):
        commands = self.__send_request(
            "PUT", f"/guilds/{guild.id}/commands", commands
        )

        return commands

    def get_guild_permissions(self, guild):
        permissions = self.__send_request(
            "GET", f"/guilds/{guild.id}/commands/permissions"
        )

        return permissions

    def get_command_permissions(self, guild, id_):
        permissions = self.__send_request(
            "GET", f"/guilds/{guild.id}/commands/{id_}/permissions"
        )

        return permissions

    def edit_command_permissions(self, guild, id_, permissions):
        permissions = self.__send_request(
            "GET", f"/guilds/{guild.id}/commands/{id_}/permissions",
            permissions
        )

        return permissions

    def batch_command_permissions(self, guild, permissions):
        permissions = self.__send_request(
            "PUT", f"/guilds/{guild.id}/commands/permissions", permissions
        )

        return permissions


class InteractionEventParser(GatewayEventParser):
    def on_interaction_create(self, payload):
        obj = Context(self.client, payload)
        return obj


class InteractionEventHandler(MethodEventHandler):
    def on_interaction_create(self, obj):
        self.client.command_manager.execute(obj)
