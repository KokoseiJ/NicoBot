#
# NicoBot is Nicovideo Player bot for Discord, written from the scratch.
# This file is part of NicoBot.
#
# Copyright (C) 2020 Wonjun Jung (KokoseiJ)
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

from .user import User
from .JSONObject import JSONObject

TYPES = ["GUILD_TEXT", "DM", "GUILD_VOICE", "GROUP_DM ", "GUILD_CATEGORY",
         "GUILD_NEWS", "GUILD_STORE"]

KEY_LIST = ["id", "type", "guild_id", "position", "permission_overwrites",
            "name", "topic", "nsfw", "last_message_id", "bitrate",
            "user_limit", "rate_limit_per_user", "recipients", "icon",
            "owner_id", "application_id", "parent_id", "last_pin_timestamp"]


def get_channel(json, client, guild=None, type=None):
    if type is None:
        type = json['type']

    if type == 0:
        return GuildTextChannel(json, client, guild)
    elif type == 1:
        return DMChannel(json, client)
    elif type == 2:
        return GuildVoiceChannel(json, client, guild)
    elif type == 3:
        return GroupDMChannel(json, client)
    elif type == 4:
        return ChannelCategory(json, client)
    elif type == 5:
        return GuildNewsChannel(json, client, guild)
    elif type == 6:
        return GuildStoreChannel(json, client, guild)
    else:
        raise NotImplementedError(f"Type {type} is not implemented")


class Channel(JSONObject):
    def __init__(self, json, client):
        super().__init__(json, KEY_LIST)
        self.client = client


class DMChannel(Channel):
    def __init__(self, json, client):
        super().__init__(json, client)
        self.recipients = {
            user['id']: User(user, client) for user in self.recipients}

    def __repr__(self):
        user = self.recipients.values()[0]
        name = user.username
        disc = user.discriminator
        return self._get_repr(f"{name}#{disc}({self.id})")


class GroupDMChannel(DMChannel):
    def __init__(self, json, client):
        super().__init__(json, client)
        self.owner = client.recipients.get(self.owner_id)

    def __repr__(self):
        return self._get_repr(f"{self.name}({self.id})")


class GuildChannel(Channel):
    def __init__(self, json, client, guild=None):
        super().__init__(json, client)

        if guild is not None:
            self.guild = guild
        else:
            self.guild = client.guilds.get(self.guild_id)

        if self.parent_id is not None:
            channels = self.guild.channels
            if isinstance(channels, list):
                self.parent = [Channel(chn, self) for chn in channels
                               if chn['id'] == self.parent_id][0]
            else:
                self.parent = self.guild.channels.get(self.id)
        else:
            self.parent = None

    def __repr__(self):
        return self._get_repr(f"{self.guild.name}:{self.name}({self.id})")


class ChannelCategory(GuildChannel):
    pass


class GuildTextChannel(GuildChannel):
    pass


class GuildNewsChannel(GuildTextChannel):
    pass


class GuildVoiceChannel(GuildChannel):
    pass


class GuildStoreChannel(GuildChannel):
    pass
