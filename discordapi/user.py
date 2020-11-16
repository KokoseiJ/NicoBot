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


class User:
    def __init__(self, obj):
        # TODO: Add function to retrieve avatar url
        self.id = obj.get("id")
        self.username = obj.get("username")
        self.discriminator = obj.get("discriminator")
        self.is_bot = obj.get("bot")
        self.is_system = obj.get("system")
        self.is_mfa_enabled = obj.get("mfa_enabled")
        self.locale = obj.get("locale")
        self.is_verified = obj.get("verified")
        self.email = obj.get("email")
        self.flags = obj.get("flags")
        self.premium_type = obj.get("premium_type")
        self.public_flags = obj.get("pubilc_flags")
        self.member = obj.get("member")

    def __repr__(self):
        return f"<User {self.username}#{self.discriminator}({self.id})>"


class GuildMember:
    def __init__(self, obj, guild):
        # TODO: Roles
        user = obj.get("user")
        self.user = User(obj.get("user")) if user is not None else None
        self.guild = guild
        self.nick = obj.get("nick")
        self.roles = obj.get("roles")
        self.joined_at = obj.get("joined_at")
        self.premium_since = obj.get("premium_since")
        self.deaf = obj.get("deaf")
        self.mute = obj.get("mute")

    def __repr__(self):
        return f"<GuildMember {self.guild.name}:{self.nick}>"
