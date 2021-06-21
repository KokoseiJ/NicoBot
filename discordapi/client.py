from .user import User
from .guild import Guild
from .gateway import DiscordGateway
from .exceptions import DiscordHTTPError
from .channel import get_channel, Channel
from .const import API_URL, LIB_NAME, LIB_VER, LIB_URL

import json
import base64
from io import BytesIO
from urllib.error import HTTPError
from urllib.request import Request, urlopen, urljoin

__all__ = ["DiscordClient"]


def construct_url(baseurl, endpoint):
    if endpoint.startswith("/"):
        endpoint = endpoint[1:]

    return urljoin(baseurl, endpoint)


class DiscordClient(DiscordGateway):
    def __init__(self, *args, **kwargs):
        super(DiscordClient, self).__init__(*args, **kwargs)

        self.headers = {
            "User-Agent": f"{LIB_NAME} ({LIB_URL}, {LIB_VER})",
            "Authorization": f"Bot {self.token}",
            "Content-Type": "application/json"
        }

    def get_user(self, id):
        user_obj = self.send_request("GET", f"/users/{id}")
        return User(user_obj)

    def get_channel(self, id):
        channel_obj = self.send_request("GET", f"/channels/{id}")
        return get_channel(self, channel_obj)

    def create_guild(self, name, icon=None, verification_level=None,
                     default_message_notifications=None,
                     explicit_content_filter=None, roles=None, channels=None,
                     afk_channel_id=None, afk_timeout=None,
                     system_channel_id=None, system_channel_flags=None):
        if icon is not None:
            if isinstance(icon, str):
                with open(icon, "rb") as f:
                    icon = f.read()
            elif isinstance(icon, BytesIO):
                icon = icon.read()

            icon = base64.b64encode(icon).decode()

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

        guild = self.send_request(
            "POST", "/guilds", postdata
        )

        return Guild(self, guild)

    def get_guild(self, id, with_counts=False):
        guild = self.send_request(
            "GET", f"/guilds/{id}?with_counts={str(with_counts).lower()}"
        )

        return Guild(self, guild)

    def get_guild_preview(self, id):
        preview = self.send_request(
            "GET", f"/guilds/{id}/preview"
        )

        return preview

    def send_request(self, method, route, data=None, expected_code=None,
                     raise_at_exc=True, baseurl=API_URL, headers=None):
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

        try:
            code = res.status
        except AttributeError:
            code = res.getstatus()

        rawdata = res.read()
        if not rawdata:
            resdata = None
        else:
            resdata = json.loads(rawdata)

        if raise_at_exc:
            if (expected_code is not None and code != expected_code) or exc:
                raise DiscordHTTPError(
                    resdata['code'], resdata['message'], res
                )

        return resdata
