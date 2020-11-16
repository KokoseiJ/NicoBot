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

from discordapi import API_URL
from discordapi.user import GuildMember
from discordapi.util import get_channel

import json
import urllib.request
from urllib.parse import urljoin


class PartialGuild:
    def __init__(self, obj, client):
        self.client = client
        self.id = obj.get("id")
        self.name = obj.get("name")
        self.icon = obj.get("icon")
        self.is_owner = obj.get("owner")
        self.permission = obj.get("permissions")
        self.features = obj.get("features")

    def get_channels(self):
        endpoint = urljoin(API_URL, f"guilds/{self.id}/channels")

        req = urllib.request.Request(endpoint, headers=self.client.header)
        with urllib.request.urlopen(req) as res:
            if res.status != 200:
                raise ValueError(f"Server returned code {res.status}.\n"
                                 f"Body: {res.read().encode()}")
            obj_list = json.loads(res.read())
            return [get_channel(obj, self) for obj in obj_list]

    def __repr__(self): return f'<PartialGuild {self.name}({self.id})>'


class Guild:
    def __init__(self, obj, client):
        # TODO: make function to retrieve image url
        # TODO: Roles, Emojis, Voice state, presences
        self.client = client
        self.obj = obj
        self.id = obj.get("id")
        self.name = obj.get("name")
        self.is_owner = obj.get("owner")
        self.owner_id = obj.get("owner_id")
        self.permissions = obj.get("permissions")
        self.region = obj.get("region")
        self.channels = [
            get_channel(channel, self) for channel in obj.get("channels")]\
            if obj.get("channels") is not None else None
        self.afk_channel = self.get_channel(obj.get("afk_channel_id"))
        self.afk_timeout = obj.get("afk_timeout")
        self.system_channel = self.get_channel(obj.get("systen_channel_id"))
        self.system_channel_flags = obj.get("system_channel_flags")
        self.widget_enabled = obj.get("widget_enabled")
        self.widget_channel = self.get_channel(obj.get("widget_channel_id"))
        self.rules_channel = self.get_channel(obj.get("rules_channel_id"))
        self.public_updates_channel = self.get_channel(
            obj.get("public_updates_channel_id"))
        self.verification_level = obj.get("verification_level")
        self.default_msg_notification = obj.get("default_message_notification")
        self.explicit_content_filter = obj.get("explicit_content_filter")
        self.roles = obj.get("roles")
        self.emojis = obj.get("emojis")
        self.features = obj.get("features")
        self.mfa_level = obj.get("mfa_level")
        self.application_id = obj.get("application_id")
        self.joined_at = obj.get("joined_at")
        self.large = obj.get("large")
        self.unavailable = obj.get("unavailable")
        self.member_count = obj.get("member_count")
        self.voice_states = obj.get("voice_states")
        self.members = [GuildMember(member, self)
                        for member in obj.get("members")]\
            if obj.get("members") is not None else None
        self.presences = obj.get("presences")
        self.max_presences = obj.get("max_presences")
        self.max_members = obj.get("max_members")
        self.vanity_url_code = obj.get("vanity_url_code")
        self.description = obj.get("description")
        self.premium_tier = obj.get("premium_tier")
        self.premium_sub_count = obj.get("premium_subscription_count")
        self.preferred_locale = obj.get("preferred_locale")
        self.max_video_channel_users = obj.get("max_video_channel_users")
        self.approx_member_count = obj.get("approximate_member_count")
        self.approx_presence_count = obj.get("approximate_presence_count")

    def get_owner(self):
        return self.client.get_user(self.owner_id)

    def get_channel(self, id):
        channel = [chan for chan in self.channels if chan.id == id]
        return channel[0] if channel else None

    def __repr__(self): return f'<Guild {self.name}({self.id})>'
