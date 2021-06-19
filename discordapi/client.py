from .channel import get_channel
from .gateway import DiscordGateway
from .const import API_URL, LIB_NAME, LIB_VER, LIB_URL

import json
from urllib.error import HTTPError
from urllib.request import Request, urlopen, urljoin


def construct_url(baseurl, endpoint):
    if endpoint.startswith("/"):
        endpoint = endpoint[1:]

    return urljoin(baseurl, endpoint)


class DiscordHTTPError(Exception):
    def __init__(self, code, message, response):
        self.code = code
        self.message = message
        self.response = response

        self.args = (f"{code}: {message}",)


class DiscordClient(DiscordGateway):
    def __init__(self, *args, **kwargs):
        super(DiscordClient, self).__init__(*args, **kwargs)

        self.headers = {
            "User-Agent": f"{LIB_NAME} ({LIB_URL}, {LIB_VER})",
            "Authorization": f"Bot {self.token}",
            "Content-Type": "application/json"
        }

    def get_channel(self, id):
        channel_obj = self.send_request("GET", f"/channels/{id}")
        return get_channel(self, channel_obj)

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
