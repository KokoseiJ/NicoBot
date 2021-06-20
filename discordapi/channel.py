from .user import User
from .message import Message
from .dictobject import DictObject

import json
import base64
from io import IOBase
from urllib.parse import quote as urlencode

KEYLIST = ["id", "type", "guild_id", "position", "permission_overwrites",
           "name", "topic", "nsfw", "last_message_id", "bitrate", "user_limit",
           "rate_limit_per_user", "recipients", "icon", "owner_id",
           "application_id", "parent_id", "last_pin_timestamp", "rtc_region",
           "video_quality_mode", "message_count", "member_count",
           "thread_metadata", "member", "default_auto_archive_duration?"]


GUILD_TEXT = 0
DM = 1
GUILD_VOICE = 2
GROUP_DM = 3
GUILD_CATEGORY = 4
GUILD_NEWS = 5
GUILD_STORE = 6
GUILD_NEWS_THREAD = 10
GUILD_PUBLIC_THREAD = 11
GUILD_PRIVATE_THREAD = 12
GUILD_STAGE_VOICE = 13


def get_channel(client, data):
    type = data['type']

    if type == GUILD_TEXT:
        return GuildTextChannel(client, data)
    elif type == DM:
        return DMChannel(client, data)
    elif type == GUILD_VOICE:
        return GuildVoiceChannel(client, data)
    elif type == GROUP_DM:
        return GroupDMChannel(client, data)
    else:
        return Channel(client, data)


class Channel(DictObject):
    def __init__(self, client, data):
        super(Channel, self).__init__(data, KEYLIST)

        self.client = client

    def modify(self, postdata):
        postdata = {
            key: value
            for key, value in postdata.items()
            if value is not None
        }

        channel_obj = self.client.send_request(
            "PATCH", f"/channels/{self.id}", postdata
        )

        self.__init__(self.client, channel_obj)

        return self

    def delete(self):
        self.client.send_request("DELETE", f"/channels/{self.id}")

    def get_messages(self, limit=None, around=None, before=None, after=None):
        getdata = {
            "limit": limit,
            "around": around,
            "before": before,
            "after": after
        }

        messages = self.client.send_request(
            "GET", f"/channels/{self.id}/messages", getdata
        )

        return [Message(message) for message in messages]

    def get_message(self, id):
        message = self.send_request(
            "GET", f"/channels/{self.id}/messages/{id}"
        )

        return Message(message)

    def send_message(self, content=None, tts=None, file=None, embeds=None,
                     allowed_mentions=None, message_reference=None,
                     components=None):
        # TODO: implement multipart/form-data
        postdata = {
            "content": content,
            "tts": tts,
            "file": file,
            "embeds": embeds,
            "allowed_mentions": allowed_mentions,
            "message_reference": message_reference,
            "components": components
        }

        message = self.client.send_request(
            "POST", f"/channels/{self.id}/messages", postdata
        )

        return Message(message)

    def edit_message(self, message, content=None, file=None, embeds=None,
                     flags=None, allowed_mentions=None, attachments=None,
                     components=None):
        # TODO: implement multipart/form-data

        if isinstance(message, Message):
            message = message.id

        postdata = {
            "content": content,
            "file": file,
            "embeds": embeds,
            "flags": flags,
            "allowed_mentions": allowed_mentions,
            "attachments": attachments,
            "components": components
        }

        message = self.client.send_request(
            "PATCH", f"/channels/{self.id}/messages/{message}", postdata
        )

        return Message(message)

    def delete_message(self, message):
        if isinstance(message, Message):
            message = message.id

        self.client.send_request(
            "DELETE", f"/channels/{self.id}/messages/{message}"
        )

    def delete_messages(self, messages):
        messages = [message.id if isinstance(message, Message) else message
                    for message in messages]
        postdata = {
            "messages": messages
        }

        self.client.send_request(
            "POST", f"/channels/{self.id}/messages/bulk-delete", postdata
        )

    def typing(self):
        self.client.send_request(
            "POST", f"/channels/{self.id}/typing"
        )

    def get_pinned_messages(self):
        messages = self.client.send_request(
            "GET", f"/channels/{self.id}/pins"
        )

        return [Message(message) for message in messages]

    def pin_message(self, message):
        if isinstance(message, Message):
            message = message.id

        self.client.send_request(
            "PUT", f"/channels/{self.id}/pins/{message}"
        )

    def unpin_message(self, message):
        if isinstance(message, Message):
            message = message.id

        self.client.send_request(
            "DELETE", f"/channels/{self.id}/pins/{message}"
        )

    def react(self, message, emoji, urlencoded=False):
        if isinstance(message, Message):
            message = message.id
        if not urlencoded:
            emoji = urlencode(emoji)

        self.client.send_request(
            "PUT",
            f"/channels/{self.id}/messages/{message}/reactions/{emoji}/@me"
        )

    def delete_my_reaction(self, message, emoji, urlencoded=False):
        if isinstance(message, Message):
            message = message.id
        if not urlencoded:
            emoji = urlencode(emoji)

        self.client.send_request(
            "DELETE",
            f"/channels/{self.id}/messages/{message}/reactions/{emoji}/@me"
        )

    def delete_others_reaction(self, message, emoji, user, urlencoded=False):
        if isinstance(message, Message):
            message = message.id
        if isinstance(message, User):
            user = user.id
        if not urlencoded:
            emoji = urlencode(emoji)

        self.client.send_request(
            "DELETE",
            f"/channels/{self.id}/messages/{message}/reactions/{emoji}/{user}"
        )

    def get_reactions(self, message, emoji, limit=None, after=None,
                      urlencoded=False):
        if isinstance(message, Message):
            message = message.id
        if not urlencoded:
            emoji = urlencode(emoji)

        getdata = {
            "after": after,
            "urlencoded": urlencoded
        }

        users = self.client.send_request(
            "GET", f"/channels/{self.id}/messages/{message}/reactions", getdata
        )

        return [User(user) for user in users]

    def delete_all_reactions(self, message, emoji, urlencoded=False):
        if isinstance(message, Message):
            message = message.id
        if not urlencoded:
            emoji = urlencode(emoji)

        self.client.send_request(
            "DELETE",
            f"/channels/{self.id}/messages/{message}/reactions/{emoji}"
        )


class DMChannel(Channel):
    pass


class GroupDMChannel(DMChannel):
    def __init__(self, client, data):
        super(DMChannel, self).__init__(client, data)
        self.recipients = [User(client, user) for user in self.recipients]

    def modify(self, name=None, icon=None):
        if isinstance(icon, str):
            with open(icon, "rb") as f:
                icon = base64.b64encode(f.read())
        elif isinstance(icon, IOBase):
            icon = base64.b64encode(f.read())
        elif isinstance(icon, bytes):
            icon = base64.b64encode(icon)

        postdata = json.dumps({
            "name": name,
            "icon": icon
        })

        return super(GroupDMChannel, self).modify(postdata)


class GuildChannel(Channel):
    def __init__(self, client, data):
        super(Channel, self).__init__(client, data)
        self.guild = self.client.guilds.get(self.guild_id)
        self.parent = self.guild.channels.get(self.parent_id)

    def edit_permission(self, id, allow=None, deny=None, type=None):
        putdata = {
            "allow": allow,
            "deny": deny,
            "type": type
        }

        self.client.send_request(
            "PUT", f"/channels/{self.id}/permissions/{id}", putdata
        )

    def remove_permission(self, id):
        self.client.send_request(
            "DELETE", f"/channels/{self.id}/permissions/{id}"
        )

    def get_invites(self):
        invites = self.client.send_request(
            "POST", f"/channels/{self.id}/invites"
        )
        return invites

    def invite(self, max_age=None, max_uses=None, temporary=None, unique=None,
               target_type=None, target_user_id=None):
        postdata = {
            "max_age": max_age,
            "max_uses": max_uses,
            "temporary": temporary,
            "unique": unique,
            "target_type": target_type,
            "target_user_id": target_user_id,
        }
        invite = self.client.send_request(
            "POST", f"/channels/{self.id}/invites", postdata
        )
        return invite


class GuildTextChannel(GuildChannel):
    def modify(self, name=None, position=None, topic=None, nsfw=None,
               rate_limit_per_user=None, permission_overwrites=None,
               parent_id=None):
        postdata = {
            "name": name,
            "position": position,
            "topic": topic,
            "nsfw": nsfw,
            "rate_limit_per_user": rate_limit_per_user,
            "permission_overwrites": permission_overwrites,
            "parent_id": parent_id
        }

        return super(GuildTextChannel, self).modify(postdata)

    def crosspost(self, message):
        if isinstance(message, Message):
            message = message.id
        rtnmsg = self.client.send_request(
            "POST", f"/channels/{self.id}/messages/{message}/crosspost"
        )
        return Message(rtnmsg)

    def follow_news_channel(self, id):
        return self.client.send_request(
            "POST", f"/channels/{self.id}/followers"
        )


class GuildVoiceChannel(GuildChannel):
    def modify(self, name=None, position=None, bitrate=None, user_limit=None,
               permission_overwrites=None, parent_id=None, rtc_region=None,
               video_quality_mode=None):
        postdata = {
            "name": name,
            "position": position,
            "bitrate": bitrate,
            "user_limit": user_limit,
            "permission_overwrites": permission_overwrites,
            "parent_id": parent_id,
            "rtc_region": rtc_region,
            "video_quality_mode": video_quality_mode
        }

        return super(GuildVoiceChannel, self).modify(postdata)
