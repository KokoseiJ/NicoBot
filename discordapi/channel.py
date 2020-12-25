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


def get_channel(data, client, guild=None, type=None):
    if type is None:
        type = data['type']

    if type == 0:
        return GuildTextChannel(data, client, guild)
    elif type == 1:
        return DMChannel(data, client)
    elif type == 2:
        return GuildVoiceChannel(data, client, guild)
    elif type == 3:
        return GroupDMChannel(data, client)
    elif type == 4:
        return ChannelCategory(data, client)
    elif type == 5:
        return GuildNewsChannel(data, client, guild)
    elif type == 6:
        return GuildStoreChannel(data, client, guild)
    else:
        raise NotImplementedError(f"Type {type} is not implemented")


class Channel(JSONObject):
    def __init__(self, data, client):
        super().__init__(data, KEY_LIST)
        self.client = client

    def send(self, content=None, tts=False, embed=None, mentions=None,
             reference=None, _json=None):
        from .message import Message

        if _json is not None:
            data = _json
        else:
            data = {
                "content": content,
                "tts": tts,
                "embed": embed,
                "allowed_mentions": mentions,
                "message_reference": reference
            }

        data, _, _ = self.client._request(
            f"channels/{self.id}/messages", "POST", data)

        return Message(data, self.client)


class DMChannel(Channel):
    def __init__(self, data, client):
        super().__init__(data, client)
        self.recipients = {
            user['id']: User(user, client) for user in self.recipients}

    def __repr__(self):
        user = self.recipients.values()[0]
        name = user.username
        disc = user.discriminator
        return self._get_repr(f"{name}#{disc}({self.id})")


class GroupDMChannel(DMChannel):
    def __init__(self, data, client):
        super().__init__(data, client)
        self.owner = client.recipients.get(self.owner_id)

    def __repr__(self):
        return self._get_repr(f"{self.name}({self.id})")


class GuildChannel(Channel):
    def __init__(self, data, client, guild=None):
        super().__init__(data, client)

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
