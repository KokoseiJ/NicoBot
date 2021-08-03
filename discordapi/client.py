#
# NicoBot is Nicovideo Player bot for Discord, written from the scratch.
# This file is part of NicoBot.
#
# Copyright (C) 2021 Wonjun Jung (KokoseiJ)
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

from .file import File
from .user import User
from .guild import Guild
from .channel import Channel
from .gateway import DiscordGateway
from .util import EMPTY, clear_postdata
from .ratelimit import RateLimitHandler
from .exceptions import DiscordHTTPError
from .channel import get_channel as _get_channel
from .const import API_URL, LIB_NAME, LIB_VER, LIB_URL

import json
import time
import base64
import logging
from urllib.error import HTTPError
from urllib.request import Request, urlopen, urljoin

__all__ = ["DiscordClient"]

logger = logging.getLogger(LIB_NAME)


def construct_url(baseurl, endpoint):
    if endpoint.startswith("/"):
        endpoint = endpoint[1:]

    return urljoin(baseurl, endpoint)


class DiscordClient(DiscordGateway):
    """Class which handles sending events to Discord.

    Attributes:
        headers:
            Headers to be used when sending HTTP request.
        _activities:
            Activity objects used when sending UPDATE_PRESENCE event- This
            attribute is required as changing status resets the activities.
        ratelimit_handler:
            handler used to handle rate limit accordingly.
    """
    def __init__(self, token, handler=None, intents=32509, name="main"):
        super(DiscordClient, self).__init__(token, handler, intents, name)

        self.headers = {
            "User-Agent": f"{LIB_NAME} ({LIB_URL}, {LIB_VER})",
            "Authorization": f"Bot {self.token}",
            "Content-Type": "application/json"
        }
        self._activities = ()
        self.ratelimit_handler = RateLimitHandler()

    def get_guild(self, id_):
        return self.guilds.get(id_)

    def get_channel(self, id_):
        return {
            x: y for guild in self.guilds for x, y in guild.channels.items()
        }.get(id_)

    def get_user(self, id_):
        return {
            x: y for guild in self.guilds for x, y in guild.users.items()
        }.get(id_)

    def update_presence(self, activities=None, status=None, afk=False,
                        since=None):
        """Updates the presence- This includes its status and activities.

        You can use this method to change the bot's status, as well as its
        activities.
        Activities will be stored on ._activities attribute and will carry over
        other changes. If you want to reset the Activities, pass an empty list
        or tuple to activities argument.

        Args:
            activities:
                A list/tuple of array, or a single object of Activity object
                in dict type. This will be saved into ._activities attribute.
            status:
                Status string. Possible values are;
                online, idle, dnd, invisible, offline.
        """
        if since is None:
            since = time.time() * 1000
        if activities is not None:
            if isinstance(activities, list):
                activities = tuple(activities)
            elif not isinstance(activities, tuple):
                activities = (activities,)
            self._activities = activities
        data = self._get_payload(
            self.PRESENCE_UPDATE,
            activities=self._activities,
            status=status,
            afk=afk,
            since=since
        )

        data['d'] = clear_postdata(data['d'])

        self.send(data)

    def update_voice_state(self, guild_id, channel_id=None, mute=False,
                           deaf=False):
        data = self._get_payload(
            self.VOICE_STATE_UPDATE,
            guild_id=guild_id,
            channel_id=channel_id,
            self_mute=mute,
            self_deaf=deaf
        )

        self.send(data)

    def request_guild_member(self, guild_id, query=EMPTY, limit=EMPTY,
                             presences=EMPTY, user_ids=EMPTY, nonce=EMPTY):
        data = self._get_payload(
            self.REQUEST_GUILD_MEMBERS,
            guild_id=guild_id,
            query=query,
            limit=limit,
            presences=presences,
            user_ids=user_ids,
            nonce=nonce
        )

        data['d'] = clear_postdata(data['d'])

        self.send(data)

    def modify_user(self, username=EMPTY, avatar=EMPTY):
        return self.user.modify_user(username, avatar)

    def leave_guild(self, guild):
        return self.user.leave_guild(guild)

    def create_dm(self, user):
        return self.user.create_dm(user)

    def get_connections(self):
        return self.user.get_connections()

    def fetch_user(self, id_):
        user_obj = self.send_request("GET", f"/users/{id_}")
        return User(self, user_obj)

    def fetch_channel(self, id_):
        channel_obj = self.send_request("GET", f"/channels/{id_}")
        return _get_channel(self, channel_obj)

    def create_guild(self, name, icon=None, verification_level=EMPTY,
                     default_message_notifications=EMPTY,
                     explicit_content_filter=EMPTY, roles=EMPTY,
                     channels=EMPTY, afk_channel_id=EMPTY, afk_timeout=EMPTY,
                     system_channel_id=EMPTY, system_channel_flags=EMPTY):
        if icon is not None:
            if not isinstance(icon, File):
                raise ValueError(f"icon should be File, not {type(icon)}")
            icon = base64.b64encode(icon.read()).decode()

        channels = [channel._json if isinstance(channel, Channel) else channel
                    for channel in channels]

        postdata = {
            "name": name,
            "icon": icon,
            "verification_level": verification_level,
            "default_message_notifications": default_message_notifications,
            "explicit_content_filter": explicit_content_filter,
            "roles": roles,
            "channels": channels,
            "afk_channel_id": afk_channel_id,
            "afk_timeout": afk_timeout,
            "system_channel_id": system_channel_id,
            "system_channel_flags": system_channel_flags,
        }

        postdata = clear_postdata(postdata)

        guild = self.send_request(
            "POST", "/guilds", postdata
        )

        return Guild(self, guild)

    def fetch_guild(self, id_, with_counts=False):
        """Returns guild object.

        This method sends request to HTTP API to fetch the object. Most of the
        time, this is probably not what you want. Try to find the guild in
        .guilds Attribute by calling `client.guilds.get(guild_id)`.
        """
        guild = self.send_request(
            "GET", f"/guilds/{id_}?with_counts={str(with_counts).lower()}"
        )

        return Guild(self, guild)

    def get_guild_preview(self, id_):
        preview = self.send_request(
            "GET", f"/guilds/{id_}/preview"
        )

        return preview

    def send_request(self, method, route, data=None, expected_code=None,
                     raise_at_exc=True, baseurl=API_URL, headers=None):
        """Sends HTTP API request.

        It sends the request, parses result data, checks ratelimit, and returns
        result data in JSON format.

        Args:
            method:
                HTTP method to use- e.g. GET, POST, DELETE, etc...
            route:
                API subdirectory to send request to. e.g. /channels/id
            data:
                POST data to send to, as a dictionary, refer to urllib.request
                for details.
            expected_code:
                HTTP return code to check for. If this code mismatches and
                raise_at_exc is true, This will raise DiscordHTTPError.
            raise_at_exc:
                Whether or not to throw exception when urllib.request raises
                HTTPError or return code is not what we were expecting.
                If this is true, DiscordHTTPError will be raised.
            baseurl:
                Base URL to construct full URL with. Defaluts to Discord API
                endpoint.
            headers:
                Headers to use when sending requests. It contains User-Agent,
                Autorization, Content-Type by default. Should be used if
                Content-Type is not application/json .

        Returns:
            Dict made out of JSON object returned from API.

        Raises:
            DiscordHTTPError:
                Raised when HTTPError is raised, or unexpected code is returned
        """
        if baseurl is None:
            baseurl = API_URL

        self.ratelimit_handler.check(route)
        
        res, exc = self._send_request(method, route, data, baseurl, headers)

        try:
            code = res.status
        except AttributeError:
            code = res.getstatus()

        rawdata = res.read()
        if not rawdata:
            resdata = None
        else:
            resdata = json.loads(rawdata)
        
        logger.debug(f"Received from HTTP API: {resdata}")

        if code == 429:
            limit = time.time() + resdata['retry_after']
            _route = "global" if resdata['global'] else route
            self.ratelimit_handler.set_limit(_route, limit)

            return self.send_request(method, route, data, expected_code,
                                     raise_at_exc, baseurl, headers)

        bucket = res.headers.get("X-RateLimit-Bucket")
        if bucket is not None and\
                not self.ratelimit_handler.is_in_bucket_map(route):
            self.ratelimit_handler.register_bucket(route, bucket)

        if raise_at_exc and \
                ((expected_code is not None and code != expected_code) or exc):
            raise DiscordHTTPError(
                resdata['code'], resdata['message'], res
            )

        return resdata

    def _send_request(self, method, route, data=None, baseurl=API_URL,
                      headers=None):
        """Returns Response object directly.

        Args:
            method:
                HTTP method to use- e.g. GET, POST, DELETE, etc...
            route:
                API subdirectory to send request to. e.g. /channels/id
            data:
                POST data to send to, as a dictionary, refer to urllib.request
                for details.
            baseurl:
                Base URL to construct full URL with. Defaluts to Discord API
                endpoint.
            headers:
                Headers to use when sending requests. It contains User-Agent,
                Autorization, Content-Type by default. Should be used if
                Content-Type is not application/json.

        Returns:
            A tuple of (Response, exc) where exc determines whether an
            exception was occured or not.
            If HTTPError was thrown, Response object would be a catched
            exception, but there's no difference in its functionality.
        """
        url = construct_url(API_URL, route)

        if isinstance(data, dict):
            data = json.dumps(data)
        if isinstance(data, str):
            data = data.encode()

        req_headers = self.headers
        if headers is not None:
            req_headers.update(headers)

        req = Request(url, data, req_headers, method=method)

        exc = False
        try:
            res = urlopen(req)
        except HTTPError as e:
            exc = True
            res = e

        return res, exc
