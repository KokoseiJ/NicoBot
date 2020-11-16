# NicoBot - Nicovideo player bot for discord, written from the scratch
# Copyright (C) 2020 Wonjun Jung (Kokosei J)
#
#    This program is free software: you can redistribute it and/or modify
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

from discordapi import API_URL

import json
import urllib.request
from urllib.parse import urljoin


class Channel:
    def __init__(self, obj):
        self.id = obj.get("id")
        self.type = obj.get("type")
        self.last_message_id = obj.get("last_message_id")


class DMChannel(Channel):
    def __init__(self, obj):
        # TODO: Change objects in recipients to User objects
        #       when it gets implemented
        #       change repl too while you're at it ;) -10/26
        super().__init__(obj)
        self.recipients = obj.get("recipients")


class GroupDMChannel(DMChannel):
    def __init__(self, obj):
        # TODO: Add owner property
        super().__init__(obj)
        self.name = obj.get("name")
        self.icon = obj.get("icon")
        self.owner_id = obj.get("owner_id")
        self.application_id = obj.get("application_id")


class GuildChannel(Channel):
    def __init__(self, obj, guild=None):
        super().__init__(obj)
        self.guild = guild
        self.guild_id = obj.get("guild_id")
        self.name = obj.get("name")
        self.position = obj.get("position")
        self.permission_overwrites = obj.get("permission_overwrites")
        self.is_nsfw = obj.get("nsfw")
        self.parent_id = obj.get("parent_id")

    def __repr__(self):
        return f"<{self.__class__.__name__} " +\
               f"{self.guild.name}:{self.name}({self.id})>"


class GuildTextChannel(GuildChannel):
    def __init__(self, obj, guild=None):
        super().__init__(obj, guild)
        self.topic = obj.get("topic")
        self.rate_limit = obj.get("rate_limit_per_user")
        self.last_message_id = obj.get("last_message_id")
        self.last_pin_timestamp = obj.get("last_pin_timestamp")

    def send_message(self, content, nonce=None, tts=False, file=None,
                     embed=None, allowed_mentions=None):
        endpoint = urljoin(API_URL, f"channels/{self.id}/messages")
        header = self.guild.client.header.copy()
        header.update({"Content-Type": "application/json"})
        req = urllib.request.Request(
            endpoint,
            json.dumps({
                "content": content,
                "nonce": nonce,
                "tts": tts,
                "embed": embed,
                "allowed_mentions": allowed_mentions
            }).encode(),
            header
        )
        with urllib.request.urlopen(req) as res:
            if res.status != 200:
                raise ValueError(f"Server returned code {res.status}.\n"
                                 f"Body: {res.read().encode()}")


class GuildNewsChannel(GuildTextChannel):
    pass


class GuildVoiceChannel(GuildChannel):
    def __init__(self, obj, guild=None):
        super().__init__(obj, guild)
        self.bitrate = obj.get("bitrate")
        self.user_limit = obj.get("user_limit")


class GuildCategory(GuildChannel):
    pass


class GuildStoreChannel(GuildChannel):
    pass
