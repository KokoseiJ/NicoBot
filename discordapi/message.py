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

from .user import User
from .member import Member
from .const import EMPTY, LIB_NAME
from .dictobject import DictObject
from .exceptions import DiscordError

import logging

__all__ = ["Message"]

KEYLIST = [
    "id",
    "channel_id",
    "guild_id",
    "author",
    "member",
    "content",
    "timestamp",
    "edited_timestamp",
    "tts",
    "mention_everyone",
    "mentions",
    "mention_roles",
    "mention_channels",
    "attachments",
    "embeds",
    "reactions",
    "nonce",
    "pinned",
    "webhook_id",
    "type",
    "activity",
    "application",
    "application_id",
    "message_reference",
    "flags",
    "stickers",
    "referenced_message",
    "interaction",
    "thread",
    "components",
]

logger = logging.getLogger(LIB_NAME)


class Message(DictObject):
    def __init__(self, client, data):
        super(Message, self).__init__(data, KEYLIST)
        self.client = client

        if self.channel_id:
            self.channel = client.get_channel(self.channel_id)
            if self.channel is None:
                logger.warning("Failed to locally retrieve channel <%s>! "
                               "sending HTTP request...", self.channel_id)
                self.channel = client.fetch_channel(self.channel_id)
                if self.channel is None:
                    raise DiscordError("Failed to retrieve channel "
                                       f"<{self.channel_id}>")

        if self.guild_id:
            self.guild = client.get_guild(self.guild_id)
            if self.guild is None:
                logger.error("Failed to retrieve guild <%s>! ",
                             self.guild_id)
        else:
            self.guild = None

        if self.channel_id:
            if self.guild is not None:
                self.channel = self.guild.get_channel(self.channel_id)
            else:
                self.channel = client.get_channel(self.channel_id)
            if self.channel is None:
                logger.warning("Failed to locally retrieve channel <%s>! "
                               "sending HTTP request...", self.channel_id)
                self.channel = client.fetch_channel(self.channel_id)
                if self.channel is None:
                    raise DiscordError("Failed to retrieve channel "
                                       f"<{self.channel_id}>")

        if self.author is not None:
            self.author = User(client, self.author)
        if self.member is not None:
            self.member = Member(client, self.guild, self.member)
            self.member.user = self.author
        if self.mentions is not None:
            self.mentions = [User(client, user) for user in self.mentions]
        if self.referenced_message is not None:
            self.referenced_message = Message(client, self.referenced_message)

    def crosspost(self):
        self.channel.crosspost(self)

    def react(self, emoji, urlencoded=False):
        self.channel.react(self, emoji, urlencoded)

    def delete_my_reaction(self, emoji, urlencoded=False):
        self.channel.delete_my_reaction(self, emoji, urlencoded)

    def delete_others_reaction(self, emoji, user, urlencoded=False):
        self.channel.delete_others_reaction(self, emoji, user, urlencoded)

    def get_reactions(self, emoji, limit=EMPTY, after=EMPTY, urlencoded=False):
        self.channel.get_reactions(self, emoji, limit, after, urlencoded)

    def delete_all_reactions(self):
        self.channel.delete_all_reactions(self)

    def delete_all_reactions_for_emoji(self, emoji, urlencoded=False):
        self.channel.delete_all_reactions_for_emoji(self, emoji, urlencoded)

    def edit(
        self,
        content=EMPTY,
        file=None,
        embeds=EMPTY,
        flags=EMPTY,
        allowed_mentions=EMPTY,
        attachments=EMPTY,
        components=EMPTY,
    ):
        self.channel.edit_message(
            self,
            content,
            file,
            embeds,
            flags,
            allowed_mentions,
            attachments,
            components,
        )

    def delete(self):
        self.channel.delete_message(self)

    def pin(self):
        self.channel.pin_message(self)

    def unpin(self):
        self.channel.unpin_message(self)

    def __str__(self):
        class_name = self.__class__.__name__
        username = self.author.username
        tag = self.author.discriminator
        username_full = f"{username}#{tag}"
        return self._get_str(class_name, self.id, username_full)
