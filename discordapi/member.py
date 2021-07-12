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
            self.user = User(client, self.user)

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

    def __str__(self):
        class_name = self.__class__.__name__
        username = self.user.username
        tag = self.user.discriminator
        username_full = f"{username}#{tag}"
        return self._get_str(class_name, self.user.id, username_full)
