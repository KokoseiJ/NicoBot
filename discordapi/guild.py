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
from .const import IMAGE_URL
from .channel import get_channel
from .JSONObject import JSONObject


def get_url(hash, type, id, format="{}", size=None):
    if hash is None:
        return None

    if not format.startswith("."):
        format = f".{format}"
    if size is not None:
        if not 16 <= size <= 4096:
            raise ValueError(
                "Size should be power of two between 16 and 4096.")
        size = f"?{size}"
    else:
        size = ''

    return f"{IMAGE_URL}{type}/{id}/{hash}{format}{size}"


GUILD_KEY_LIST = ["id", "name", "icon", "icon_hash", "splash",
                  "discovery_splash", "owner", "owner_id", "permissions",
                  "region", "afk_channel_id", "afk_timeout", "widget_enabled",
                  "widget_channel_id", "verification_level",
                  "default_message_notifications", "explicit_content_filter",
                  "roles", "emojis", "features", "mfa_level", "application_id",
                  "system_channel_id", "system_channel_flags",
                  "rules_channel_id", "joined_at", "large", "unavailable",
                  "member_count", "voice_states", "members", "channels",
                  "presences", "max_presences", "max_members",
                  "vanity_url_code", "description", "banner", "premium_tier",
                  "premium_subscription_count", "preferred_locale",
                  "public_updates_channel_id", "max_video_channel_users",
                  "approximate_member_count", "approximate_presence_count"]

MEMBER_KEY_LIST = ["user", "nick", "roles", "joined_at", "premium_since",
                   "deaf", "mute", "pending"]


class Guild(JSONObject):
    def __init__(self, json, client):
        super().__init__(json, GUILD_KEY_LIST)
        self.client = client
        if self.members is not None:
            self.members = {member['user']['id']: Member(member, client)
                            for member in self.members}
            self.channels = {channel['id']: get_channel(channel, client, self)
                             for channel in self.channels}

        self.icon = get_url(self.icon, "icons", self.id)
        self.icon_hash = get_url(self.icon_hash, "icons", self.id)
        self.splash = get_url(self.splash, "splashes", self.id)
        self.discovery_splash = get_url(
            self.discovery_splash, "discovery-splashes", self.id)
        self.banner = get_url(self.banner, "banners", self.id)


class Member(JSONObject):
    def __init__(self, json, client):
        super().__init__(json, MEMBER_KEY_LIST)
        if self.user is not None:
            self.user = User(self.user, client)
