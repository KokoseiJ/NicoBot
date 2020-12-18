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

from .const import IMAGE_URL
from .JSONObject import JSONObject

KEY_LIST = ["id", "username", "discriminator", "avatar", "bot", "system",
            "mfa_enabled", "locale", "verified", "email", "flags",
            "premium_type", "public_flags"]


class User(JSONObject):
    def __init__(self, json, client):
        super().__init__(json, KEY_LIST)
        self.client = client
        self.avatar = f"{IMAGE_URL}{self.id}/{self.avatar}.{{}}"
