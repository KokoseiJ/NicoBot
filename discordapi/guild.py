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

__all__ = ["Guild"]

from .dictobject import DictObject
from .channel import Channel
from .exceptions import DiscordHTTPError

DEFAULT_KEY = ["id", "name", "icon", "icon_hash", "splash", "discovery_splash",
               "owner", "owner_id", "permissions", "region", "afk_channel_id",
               "afk_timeout", "widget_enabled", "widget_channel_id",
               "verification_level", "default_message_notifications",
               "explicit_content_filter", "roles", "emojis", "features",
               "mfa_level", "application_id", "system_channel_id",
               "system_channel_flags", "rules_channel_id", "joined_at",
               "large", "unavailable", "member_count", "voice_states",
               "members", "channels", "presences", "max_presences",
               "max_members", "vanity_url_code", "description", "banner",
               "premium_tier", "premium_subscription_count",
               "preferred_locale", "public_updates_channel_id",
               "max_video_channel_users", "approximate_member_count",
               "approximate_presence_count", "welcome_screen"]


class Guild(DictObject):
    def __init__(self, client, dictobj):
        self.client = client
        super(DictObject, self).__init__(dictobj, DEFAULT_KEY)

    def get_channels(self):
        data, status, res = self.client._request(f"guilds/{id}/channels")
        if status != 200:
            raise DiscordHTTPError(data, status, res)

        return [Channel(channel) for channel in data]
