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
from .guild import Member
from .JSONObject import JSONObject

KEY_LIST = ["id", "channel_id", "guild_id", "author", "member", "content",
            "timestamp", "edited_timestamp", "tts", "mention_everyone",
            "mentions", "mention_roles", "mention_channels", "attachments",
            "embeds", "reactions", "nonce", "pinned", "webhook_id", "type",
            "activity", "application", "message_reference", "flags",
            "stickers", "referenced_message"]


class Message(JSONObject):
    def __init__(self, json, client):
        super().__init__(json, KEY_LIST)
        self.client = client

        self.guild = client.guilds.get(self.guild_id)
        if self.guild is not None:
            self.channel = self.guild.channels.get(self.channel_id)
        else:
            self.channel = None
        self.author = User(self.author, client)
        if self.member is not None:
            self.member = Member(self.member, client)
        self.mentions = [User(user, client) for user in self.mentions]

        if self.mention_channels is not None:
            self.mention_channels = [
                client.guilds.get(data['guild_id']).channels.get(data['id'])
                for data in self.mention_channels]
        if self.referenced_message is not None:
            self.referenced_message = Message(self.referenced_message, client)

    def get_channel(self):
        channel = self.client.get_channel(self.channel_id)
        self.channel = channel
        return channel

    def send(self, content=None, tts=False, embed=None, mentions=None,
             reply=False, _json=None):
        if _json is not None:
            data = _json
        else:
            if reply:
                ref = {
                    "message_id": self.id,
                    "channel_id": self.channel_id,
                    "guild_id": self.guild_id
                }
            else:
                ref = None
            data = {
                "content": content,
                "tts": tts,
                "embed": embed,
                "allowed_mentions": mentions,
                "message_reference": ref
            }

        data, _, _ = self.client._request(
            f"channels/{self.channel_id}/messages", "POST", data)

        return Message(data, self.client)

    def edit(self, content=None, embed=None, flags=None,
             mentions=None, _json=None):
        if _json is not None:
            data = _json
        else:
            data = {
                "content": content,
                "embed": embed,
                "flags": flags,
                "allowed_mentions": mentions
            }

        data, _, _ = self.client._request(
            f"channels/{self.channel_id}/messages/{self.id}", "PATCH", data)
        return Message(data, self.client)

    def delete(self):
        self.client._request(
            f"channels/{self.channel_id}/messages/{self.id}", "DELETE")
