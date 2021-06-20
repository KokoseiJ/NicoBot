from .channel import get_channel
from .dictobject import DictObject
from .client import DiscordHTTPError

import base64
from io import BytesIO

KEYLIST = ["id", "name", "icon", "icon_hash?", "splash", "discovery_splash",
           "owner", "owner_id", "permissions", "region", "afk_channel_id",
           "afk_timeout", "widget_enabled", "widget_channel_id",
           "verification_level", "default_message_notifications",
           "explicit_content_filter", "roles", "emojis", "features",
           "mfa_level", "application_id", "system_channel_id",
           "system_channel_flags", "rules_channel_id", "joined_at", "large",
           "unavailable", "member_count", "voice_states", "members",
           "channels", "threads", "presences", "max_presences", "max_members",
           "vanity_url_code", "description", "banner", "premium_tier",
           "premium_subscription_count", "preferred_locale",
           "public_updates_channel_id", "max_video_channel_users",
           "approximate_member_count", "approximate_presence_count",
           "welcome_screen", "nsfw_level", "stage_instances"]


MEMBER_KEYLIST = ["user", "nick", "roles", "joined_at", "premium_since",
                  "deaf", "mute", "pending", "permissions"]


class Guild(DictObject):
    def __init__(self, client, data):
        super(Guild, self).__init__(data, KEYLIST)
        self.client = client

    def get_preview(self):
        return self.client.get_guild_preiew(self.id)

    def modify(self, name=None, region=None, verification_level=None,
               default_message_notifications=None,
               explicit_content_filter=None, afk_channel_id=None,
               afk_timeout=None, icon=None, owner_id=None, splash=None,
               discovery_splash=None, banner=None, system_channel_id=None,
               system_channel_flags=None, rules_channel_id=None,
               public_updates_channel_id=None, preferred_locale=None,
               features=None, description=None):
        if icon is not None:
            if isinstance(icon, str):
                with open(icon, "rb") as f:
                    icon = f.read()
            elif isinstance(icon, BytesIO):
                icon = icon.read()

            icon = base64.b64encode(icon).decode()

        postdata = {
            "name": name,
            "region": region,
            "verification_level": verification_level,
            "default_message_notifications": default_message_notifications,
            "explicit_content_filter": explicit_content_filter,
            "afk_channel_id": afk_channel_id,
            "afk_timeout": afk_timeout,
            "icon": icon,
            "owner_id": owner_id,
            "splash": splash,
            "discovery_splash": discovery_splash,
            "banner": banner,
            "system_channel_id": system_channel_id,
            "system_channel_flags": system_channel_flags,
            "rules_channel_id": rules_channel_id,
            "public_updates_channel_id": public_updates_channel_id,
            "preferred_locale": preferred_locale,
            "features": features,
            "description": description
        }

        guild = self.client.send_request(
            "PATCH", f"/guilds/{self.id}", postdata
        )

        self.__init__(self.client, guild)

        return self

    def delete(self):
        self.client.send_request(
            "DELETE", f"/guilds/{self.id}"
        )

    def get_channels(self):
        if self.channels is not None:
            return self.channels
        
        raw_channels = self.client.send_request(
            "GET", f"/guilds/{self.id}/channels"
        )

        channels = [get_channel(channel) for channel in raw_channels]
        self.channels = channels

        return channels

    def create_channel(self, name, type, topic=None, bitrate=None,
                       user_limit=None, rate_limit_per_user=None,
                       position=None, permission_overwrites=None,
                       parent_id=None, nsfw=None):
        postdata = {
            "name": name,
            "type": type,
            "topic": topic,
            "bitrate": bitrate,
            "user_limit": user_limit,
            "rate_limit_per_user": rate_limit_per_user,
            "position": position,
            "permission_overwrites": permission_overwrites,
            "parent_id": parent_id,
            "nsfw": nsfw
        }

        channel = self.client.send_request(
            "POST", f"/guilds/{self.id}/channels", postdata
        )

        return get_channel(channel)

    def modify_channel_positions(self, params={}):
        self.client.send_request(
            "PATCH", f"/guilds/{self.id}/channels", params
        )

    def get_member(self, user):
        if isinstance(user, User):
            user = user.id
        member = self.client.send_request(
            "GET", f"/guilds/{self.id}/members/{user}"
        )

        return Member(member)

    def list_members(self):
        members = self.client.send_request(
            "GET", f"/guilds/{self.id}/members"
        )

        return [Member(member) for member in members]

    def search_members(self, query=None, limit=1):
        getdata = {
            "query": query,
            "limit": limit
        }

        members = self.client.send_request(
            "GET", f"/guilds/{self.id}/members/search", getdata
        )

        return [Member(member) for member in members]

    def modify_member(self, member, nick=None, roles=None, mute=None, deaf=None,
                      channel_id=None):
        if isinstance(member, Member):
            member = member.id
        postdata = {
            "nick": nick,
            "roles": roles,
            "mute": mute,
            "deaf": deaf,
            "channel_id": channel_id 
        }

        member = self.client.send_request(
            "PATCH", f"/guilds/{self.id}/members/{member}", postdata
        )

        return Member(member)

    def change_my_nick(self, nick):
        postdata = {
            "nick": nick
        }

        nick = self.client.send_request(
            "PATCH", f"/guilds/{self.id}/members/@me/nick", postdata
        )

        return nick

    def add_role_to_member(self, member, role):
        if isinstance(member, Member):
            member = member.id
        self.client.send_request(
            "PUT", f"/guilds/{self.id}/members/{member}/roles/{role}"
        )

    def remove_role_from_member(self, member, role):
        if isinstance(member, Member):
            member = member.id
        self.client.send_request(
            "DELETE", f"/guilds/{self.id}/members/{member}/roles/{role}"
        )

    def kick_member(self, member):
        if isinstance(member, Member):
            member = member.id

        self.client.send_request(
            "DELETE", f"/guilds/{self.id}/members/{member}"
        )

    def get_bans(self):
        bans = self.client.send_request(
            "GET", f"/guilds/{self.id}/bans"
        )

        return bans

    def get_ban(self, member):
        if isinstance(member, Member):
            member = member.id

        try:
            ban = self.client.send_request(
                "GET", f"/guilds/{self.id}/bans/{member}"
            )
        except DiscordHTTPError as e:
            if e.code == 404:
                return False
            else:
                raise

        return ban

    def ban(self, member):
        if isinstance(member, Member):
            member = member.id

        ban = self.client.send_request(
            "PUT", f"/guilds/{self.id}/bans/{member}"
        )
        
        return ban

    def remove_ban(self, member):
        if isinstance(member, Member):
            member = member.id

        self.client.send_request(
            "DELETE", f"/guilds/{self.id}/bans/{member}"
        )
    
    def get_roles(self):
        roles = self.client.send_request(
            "GET", f"/guilds/{self.id}/roles"
        )

        return roles

    def create_role(self, name=None, permission=None, color=None, hoist=None,
                    mentionable=None):
        postdata = {
            "name": name,
            "permission": permission,
            "color": color,
            "hoist": hoist,
            "mentionable": mentionable
        }

        role = self.client.send_request(
            "POST", f"/guilds/{self.id}/roles", postdata
        )

        return role

    def modify_role_position(self, params):
        roles = self.client.send_request(
            "PATCH", f"/guilds/{self.id}/roles", params
        )

        return roles

    def modify_guild_role(self, role, name=None, permissions=None, color=None,
                          hoist=None, mentionable=None):
        postdata = {
            "name": name,
            "permissions": permissions,
            "color": color,
            "hoist": hoist,
            "mentionable": mentionable
        }

        role = self.client.send_request(
            "PATCH", f"/guilds/{self.id}/roles/{role}", postdata
        )

    def delete_role(self, role):
        self.client.send_request(
            "DELETE", f"/guilds/{self.id}/roles/{role}"
        )

    def get_voice_regions(self):
        regions = self.client.send_request(
            "GET", f"/guilds/{self.id}/regions"
        )

        return regions

    def get_invites(self):
        invites = self.client.send_request(
            "GET", f"/guilds/{self.id}/invites"
        )

        return invites


class Member(DictObject):
    def __init__(self, client, guild, data):
        super(Member, self).__init__(data, MEMBER_KEYLIST)
        self.client = client
        self.guild = guild
