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
from .const import EMPTY, CDN_URL
from .util import clear_postdata
from .dictobject import DictObject

import base64
from urllib.parse import urljoin

__all__ = ["User"]

KEYLIST = [
    "id",
    "username",
    "discriminator",
    "avatar",
    "bot",
    "system",
    "mfa_enabled",
    "locale",
    "verified",
    "email",
    "flags",
    "premium_type",
    "public_flags",
]

"""
It is recommended to check Official Discord documentation for these methods.
Almost every arguments in these method represent those in their API doc 1:1,
and thus I did not add further explanations about how things work.
"""


class User(DictObject):
    def __init__(self, client, data):
        super(User, self).__init__(data, KEYLIST)
        self.client = client
        self.avatar = urljoin(CDN_URL, f"avatars/{self.id}/{self.avatar}.png")

    def dm(self):
        return self.client.user.create_dm(self)

    def __str__(self):
        class_name = self.__class__.__name__
        username = self.username
        tag = self.discriminator
        username_full = f"{username}#{tag}"
        return self._get_str(class_name, self.id, username_full)


class BotUser(User):
    def modify_user(self, username=EMPTY, avatar=None):
        if avatar is not None:
            if not isinstance(avatar, File):
                raise ValueError(f"avatar should be File, not {type(avatar)}")
            avatar = base64.b64encode(avatar.read()).decode()

        postdata = {"username": username, "avatar": avatar}
        postdata = clear_postdata(postdata)

        user = self._send_request("PATCH", "", postdata)

        self.__init__(self.client, user)

        return self

    def leave_guild(self, guild):
        from .guild import Guild

        if isinstance(guild, Guild):
            guild = guild.id

        self._send_request("DELETE", f"/guilds/{guild}")

    def create_dm(self, user):
        from .channel import get_channel

        if isinstance(user, User):
            user = user.id

        postdata = {"recipient_id": user}

        channel = self._send_request("POST", "/channels", postdata)

        return get_channel(self.client, channel)

    def get_connections(self):
        connections = self._send_request("GET", "/connections")

        return connections

    def _send_request(
        self,
        method,
        route,
        data=None,
        expected_code=None,
        raise_at_exc=True,
        baseurl=None,
        headers=None,
    ):
        route = f"/users/@me{route}"
        return self.client.send_request(
            method, route, data, expected_code, raise_at_exc, baseurl, headers
        )
