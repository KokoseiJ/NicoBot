from .user import User
from .dictobject import DictObject

KEYLIST = ["user", "nick", "roles", "joined_at", "premium_since",
           "deaf", "mute", "pending", "permissions"]


class Member(DictObject):
    def __init__(self, client, guild, data):
        super(Member, self).__init__(data, KEYLIST)
        self.client = client
        self.guild = guild

        if self.user is not None:
            self.user = User(self.user)
