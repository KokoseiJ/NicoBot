from .const import EMPTY
from .util import clear_postdata
from .dictobject import DictObject

import base64
from io import BytesIO

__all__ = ["User"]

KEYLIST = ["id", "username", "discriminator", "avatar", "bot", "system",
           "mfa_enabled", "locale", "verified", "email", "flags",
           "premium_type", "public_flags"]


class User(DictObject):
    def __init__(self, client, data):
        super(User, self).__init__(data, KEYLIST)
        self.client = client

    def dm(self):
        return self.client.user.create_dm(self)


class BotUser(User):
    def modify_user(self, username=EMPTY, avatar=EMPTY):
        if isinstance(avatar, str):
            with open(avatar, "rb") as f:
                avatar = f.read()
        elif isinstance(avatar, BytesIO):
            avatar = f.read()
        avatar = base64.b64encode(avatar).decode()

        postdata = {
            "username": username,
            "avatar": avatar
        }
        postdata = clear_postdata(postdata)

        user = self.client.send_request(
            "PATCH", "/users/@me", postdata
        )

        self.__init__(self.client, user)

        return self

    def leave_guild(self, guild):
        from .guild import Guild
        if isinstance(guild, Guild):
            guild = guild.id

        self.client.send_request(
            "DELETE", f"/users/@me/guilds/{guild}"
        )

    def create_dm(self, user):
        from .channel import get_channel
        if isinstance(user, User):
            user = user.id

        postdata = {
            "recipient_id": user
        }

        channel = self.client.send_request(
            "POST", "/users/@me/channels", postdata
        )

        return get_channel(channel)

    def get_connections(self):
        connections = self.client.send_request(
            "GET", "/users/@me/connections"
        )

        return connections

    def __str__(self):
        class_name = self.__class__.__name__
        username = self.username
        tag = self.discriminator
        username_full = f"{username}#{tag}"
        return f"<{class_name} {username_full} ({self.id})>"
