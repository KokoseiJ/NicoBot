from .user import User
from .const import EMPTY
from .dictobject import DictObject

__all__ = ["Member"]

KEYLIST = ["user", "nick", "roles", "joined_at", "premium_since",
           "deaf", "mute", "pending", "permissions"]


class Member(DictObject):
    def __init__(self, client, guild, data):
        super(Member, self).__init__(data, KEYLIST)
        self.client = client
        self.guild = guild

        if self.user is not None:
            self.user = User(self.user)

    def modify(self, nick=EMPTY, roles=EMPTY, mute=EMPTY, deaf=EMPTY,
               channel_id=EMPTY):
        self.guild.modify_member(self, nick, roles, mute, deaf, channel_id)

    def add_role(self, role):
        self.guild.add_role_to_member(self, role)

    def remove_role(self, role):
        self.guild.remove_role_from_member(self, role)

    def kick(self):
        self.guild.kick(self)

    def ban(self):
        self.guild.ban(self)
