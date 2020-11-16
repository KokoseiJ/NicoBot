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

from discordapi.user import User, GuildMember


class Message:
    def __init__(self, obj, client):
        # TODO: Roles, embed, reactions
        self.id = obj.get("id")
        self.guild = client.get_guild(obj.get("guild_id")) \
            if obj.get("guild_id") is not None else None
        self.channel = self.guild.get_channel(obj.get("channel_id"))
        self.author = User(obj.get("author")) \
            if obj.get("author") is not None else None
        if obj.get("member") is not None:
            self.member = GuildMember(obj.get("member"), self.guild)
            self.member.user = self.author
        else:
            self.member = None
        self.content = obj.get("content")
        self.timestamp = obj.get("timestamp")
        self.edited_timestamp = obj.get("edited_timestamp")
        self.is_tts = obj.get("tts")
        self.mention_everyone = obj.get("mention_everyone")
        mentions = obj.get("mentions")
        self.mentions = [User(user) for user in mentions]\
            if mentions is not None else None
        self.mention_roles = obj.get("mention_roles")
        mention_channels = obj.get("mention_channels")
        self.mention_channels = [
            self.guild.get_channel(chan.id) for chan in mention_channels
        ] if mention_channels is not None else None
        attachments = obj.get("attachments")
        self.attachments = [Attachment(file) for file in attachments]\
            if attachments is not None else None
        self.embeds = obj.get("embeds")
        self.reactions = obj.get("reactions")
        self.nonce = obj.get("nonce")
        self.is_pinned = obj.get("pinned")
        self.webhook_id = obj.get("webhook_id")
        self.type = obj.get("type")
        self.activity = obj.get("activity")
        self.application = obj.get("application")
        self.message_reference = obj.get("message_reference")
        self.flags = obj.get("flags")

    def __repr__(self):
        return f"<Message {self.id}>"


class Attachment:
    def __init__(self, obj):
        self.id = obj.get("id")
        self.filename = obj.get("filename")
        self.size = obj.get("size")
        self.url = obj.get("url")
        self.proxy_url = obj.get("proxy_url")
        self.height = obj.get("height")
        self.width = obj.get("width")

    def __repr__(self):
        return f"<Attachment {self.filename}({self.id})>"
