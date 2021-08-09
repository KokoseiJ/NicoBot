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

from .file import File
from .user import User
from .const import LIB_NAME
from .message import Message
from .util import clear_postdata, get_formdata
from .dictobject import DictObject
from .const import EMPTY, VOICE_VER
from .voice import DiscordVoiceClient

import json
import base64
import logging
from queue import Queue
from urllib.parse import quote as urlencode

__all__ = ["get_channel", "Channel", "DMChannel", "GroupDMChannel",
           "GuildChannel", "GuildTextChannel", "GuildVoiceChannel"]

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

logger = logging.getLogger(LIB_NAME)

"""
It is recommended to check Official Discord documentation for these methods.
Almost every arguments in these method represent those in their API doc 1:1,
and thus I did not add further explanations about how things work.
Only few methods need being checked on its own- such as .connect method in
GuildVoiceChannel class.
"""


def get_channel(client, data, guild=None):
    _type = data['type']

    if _type == GUILD_TEXT:
        return GuildTextChannel(client, data, guild)
    elif _type == DM:
        return DMChannel(client, data)
    elif _type == GUILD_VOICE:
        return GuildVoiceChannel(client, data, guild)
    elif _type == GROUP_DM:
        return GroupDMChannel(client, data)
    else:
        logger.warning(f"Unknown Channel type {_type}")
        return Channel(client, data)


class Channel(DictObject):
    def __init__(self, client, data):
        super(Channel, self).__init__(data, KEYLIST)

        self.client = client

    def modify(self, postdata):
        postdata = clear_postdata(postdata)

        channel_obj = self._send_request(
            "PATCH", "", postdata
        )

        self.__init__(self.client, channel_obj)

        return self

    def delete(self):
        self._send_request("DELETE", "")

    def get_messages(self, limit=EMPTY, around=EMPTY, before=EMPTY,
                     after=EMPTY):
        endpoint = "/messages?"
        postdata = {
            "around": around,
            "before": before,
            "after": after,
            "limit": limit
        }
        postdata = clear_postdata(postdata)

        for key, val in postdata.items():
            endpoint += f"{key}={val}&"

        endpoint = endpoint[:-1]

        messages = self._send_request(
            "GET", endpoint
        )

        return [Message(self.client, message) for message in messages]

    def get_message(self, id_):
        message = self._send_request(
            "GET", f"/messages/{id_}"
        )

        return Message(self.client, message)

    def send(self, content=EMPTY, tts=EMPTY, file=None, embeds=EMPTY,
             allowed_mentions=EMPTY, reply_to=None,
             components=EMPTY):
        if reply_to is not None:
            if isinstance(reply_to, Message):
                reply_to = reply_to.id
            if self.guild_id is not None:
                guild_id = self.guild_id
            else:
                guild_id = None
            msg_ref = clear_postdata({
                "message_id": reply_to,
                "channel_id": self.id,
                "guild_id": guild_id
            })
        else:
            msg_ref = EMPTY

        postdata = {
            "content": content,
            "tts": tts,
            "embeds": embeds,
            "allowed_mentions": allowed_mentions,
            "message_reference": msg_ref,
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

            message = self._send_request(
                "POST", "/messages", formdata, headers=headers
            )
        else:
            message = self._send_request(
                "POST", "/messages", postdata
            )

        return Message(self.client, message)

    def edit_message(self, message, content=EMPTY, file=None, embeds=EMPTY,
                     flags=EMPTY, allowed_mentions=EMPTY, attachments=EMPTY,
                     components=EMPTY):
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
        postdata = clear_postdata(postdata)

        if file is not None:
            if not isinstance(file, File):
                raise ValueError(f"file should be File, not {type(file)}")

            content_type, formdata = get_formdata({
                "file": file,
                "payload_json": postdata
            })

            headers = {"Content-Type": content_type}

            message = self._send_request(
                "PATCH", f"/messages/{message}", formdata, headers=headers
            )
        else:
            message = self._send_request(
                "PATCH", f"/messages/{message}", postdata
            )

        return Message(self.client, message)

    def delete_message(self, message):
        if isinstance(message, Message):
            message = message.id

        self._send_request(
            "DELETE", f"/messages/{message}"
        )

    def delete_messages(self, messages):
        messages = [message.id if isinstance(message, Message) else message
                    for message in messages]
        postdata = {
            "messages": messages
        }

        self._send_request(
            "POST", "/messages/bulk-delete", postdata
        )

    def typing(self):
        self._send_request(
            "POST", "/typing"
        )

    def get_pinned_messages(self):
        messages = self._send_request(
            "GET", "/pins"
        )

        return [Message(self.client, message) for message in messages]

    def pin_message(self, message):
        if isinstance(message, Message):
            message = message.id

        self._send_request(
            "PUT", f"/pins/{message}"
        )

    def unpin_message(self, message):
        if isinstance(message, Message):
            message = message.id

        self._send_request(
            "DELETE", f"/pins/{message}"
        )

    def react(self, message, emoji, urlencoded=False):
        if isinstance(message, Message):
            message = message.id
        if not urlencoded:
            emoji = urlencode(emoji)

        self._send_request(
            "PUT",
            f"/messages/{message}/reactions/{emoji}/@me"
        )

    def delete_my_reaction(self, message, emoji, urlencoded=False):
        if isinstance(message, Message):
            message = message.id
        if not urlencoded:
            emoji = urlencode(emoji)

        self._send_request(
            "DELETE",
            f"/messages/{message}/reactions/{emoji}/@me"
        )

    def delete_others_reaction(self, message, emoji, user, urlencoded=False):
        if isinstance(message, Message):
            message = message.id
        if isinstance(message, User):
            user = user.id
        if not urlencoded:
            emoji = urlencode(emoji)

        self._send_request(
            "DELETE",
            f"/messages/{message}/reactions/{emoji}/{user}"
        )

    def get_reactions(self, message, emoji, limit=EMPTY, after=EMPTY,
                      urlencoded=False):
        if isinstance(message, Message):
            message = message.id
        if not urlencoded:
            emoji = urlencode(emoji)

        postdata = {
            "after": after,
            "limit": limit
        }
        postdata = clear_postdata(postdata)

        endpoint = f"/messages/{message}/reactions?"

        for key, val in postdata.items():
            endpoint += f"{key}={val}&"

        endpoint = endpoint[:-1]

        users = self._send_request(
            "GET", endpoint
        )

        return [User(self.client, user) for user in users]

    def delete_all_reactions(self, message):
        if isinstance(message, Message):
            message = message.id

        self._send_request(
            "DELETE",
            f"/messages/{message}/reactions"
        )

    def delete_all_reactions_for_emoji(self, message, emoji, urlencoded=False):
        if isinstance(message, Message):
            message = message.id
        if not urlencoded:
            emoji = urlencode(emoji)

        self._send_request(
            "DELETE",
            f"/messages/{message}/reactions/{emoji}"
        )

    def _send_request(self, method, route, data=None, expected_code=None,
                      raise_at_exc=True, baseurl=None, headers=None):
        route = f"/channels/{self.id}{route}"
        return self.client.send_request(
            method, route, data, expected_code, raise_at_exc, baseurl, headers
        )


class DMChannel(Channel):
    def __init__(self, client, data):
        super(DMChannel, self).__init__(client, data)
        self.recipients = [User(client, user) for user in self.recipients]


class GroupDMChannel(DMChannel):
    def modify(self, name=EMPTY, icon=None):
        if icon is not None:
            if not isinstance(icon, File):
                raise RuntimeError(f"icon should be File, not {type(icon)}")
            icon = base64.b64encode(icon.read()).decode()

        postdata = json.dumps({
            "name": name,
            "icon": icon
        })

        return super(GroupDMChannel, self).modify(postdata)


class GuildChannel(Channel):
    def __init__(self, client, data, guild=None):
        super(GuildChannel, self).__init__(client, data)

        if self.guild_id is None and guild is not None:
            self.guild_id = guild.id

    def get_guild(self):
        guild = self.client.guilds.get(self.guild_id)
        if guild is None or not guild:
            return self.client.get_guild(self.guild_id)
        else:
            return guild

    def get_parent(self):
        if self.parent_id is None:
            return None
        else:
            parent = self.get_guild().channels.get(self.parent_id)
            if parent is None:
                return self.client.get_channel(self.parent_id)
            else:
                return parent

    def edit_permission(self, id_, allow=EMPTY, deny=EMPTY, type=EMPTY):
        postdata = {
            "allow": allow,
            "deny": deny,
            "type": type
        }
        postdata = clear_postdata(postdata)

        self._send_request(
            "PUT", f"/permissions/{id_}", postdata
        )

    def remove_permission(self, id_):
        self._send_request(
            "DELETE", f"/permissions/{id_}"
        )

    def get_invites(self):
        invites = self._send_request(
            "POST", "/invites"
        )
        return invites

    def invite(self, max_age=86400, max_uses=0, temporary=False,
               unique=False, target_type=EMPTY, target_user_id=EMPTY,
               target_application_id=EMPTY):
        postdata = {
            "max_age": max_age,
            "max_uses": max_uses,
            "temporary": temporary,
            "unique": unique,
            "target_type": target_type,
            "target_user_id": target_user_id,
            "target_application_id": target_application_id
        }
        postdata = clear_postdata(postdata)
        invite = self._send_request(
            "POST", "/invites", postdata
        )
        return invite


class GuildTextChannel(GuildChannel):
    def modify(self, name=EMPTY, position=EMPTY, topic=EMPTY, nsfw=EMPTY,
               rate_limit_per_user=EMPTY, permission_overwrites=EMPTY,
               parent_id=EMPTY):
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
        rtnmsg = self._send_request(
            "POST", f"/messages/{message}/crosspost"
        )
        return Message(self.client, rtnmsg)

    def follow_news_channel(self, id_):
        postdata = {
            "webhook_channel_id": id_
        }
        return self._send_request(
            "POST", "/followers", postdata
        )


class GuildVoiceChannel(GuildChannel):
    def modify(self, name=EMPTY, position=EMPTY, bitrate=EMPTY,
               user_limit=EMPTY, permission_overwrites=EMPTY, parent_id=EMPTY,
               rtc_region=EMPTY, video_quality_mode=EMPTY):
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

    def connect(self, mute=False, deaf=False):
        """Connects the bot to the voice channel.

        This method will fire a Gateway event to initialize connection to the
        voice server, create DiscordVoiceClient object, add it to
        client.voice_clients and return the client.
        Please note that client would most likely not be ready to run when it
        gets returned- please check its availability using .is_ready method or
        .ready_to_run Event attribute. AudioPlayer will also check this.
        """
        self.client.voice_queue[self.guild_id] = Queue()
        self.client.update_voice_state(self.guild_id, self.id, mute, deaf)

        token = None
        session_id = None
        while token is None or session_id is None:
            event, payload = self.client.voice_queue[self.guild_id].get()

            if event == "VOICE_STATE_UPDATE":
                session_id = payload['session_id']

            elif event == "VOICE_SERVER_UPDATE":
                token = payload['token']
                endpoint = payload['endpoint']

        endpoint = f"wss://{endpoint}?v={VOICE_VER}"
        client = DiscordVoiceClient(
            self.client, endpoint, token, session_id, self.guild_id
        )
        self.client.voice_clients[self.guild_id] = client

        client.start()
        return client
