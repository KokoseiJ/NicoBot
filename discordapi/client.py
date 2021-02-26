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

from .gateway import DiscordGateway
from .const import INTENTS_DEFAULT, LIB_NAME, LIB_URL, LIB_VER, API_URL

import json
from urllib.parse import urljoin
from urllib.error import HTTPError
from urllib.request import Request, urlopen


class DiscordClient(DiscordGateway):
    """
    Client which implements HTTP API requests. In most circumstances, You will
    want to use this class instead of DiscordGateway.

    Attributes:
        headers:
            indicates default headers to be sent when it sends an API request.
            This includes User-Agent, and Authorization headers.
            User-Agent has a value of f"{LIB_NAME} ({LIB_URL}, {LIB_VER})", as
            the official reference states. Values are from `discordapi.const`
            module.
    """
    def __init__(self, token, handler, intents=INTENTS_DEFAULT):
        super().__init__(token, handler, intents)
        self.headers = {
            "User-Agent": f"{LIB_NAME} ({LIB_URL}, {LIB_VER})",
            "Authorization": f"Bot {self.token}"
        }

    def _request(self, endpoint, data=None, method=None, content_type=None,
                 headers={}):
        """
        Sends a request to API.

        Args:
            endpoint:
                An endpoint to send a request to.
                It shouldn't have a `/` in front of it. otherwise It would
                replace the entire URL path, resulting in an error.
            data:
                A data to be sent. It could be either None, dict, str or any
                other formats that urllib.request.Request accepts.
            method:
                A method to be used while sending a request.
                Default value is "GET", if data is not specified. if data has
                been specified, It gets set to "POST". to override this, you'll
                have to specify the method you'd like to use when calling the
                function.
            content_type:
                A content_type to be sent.
                Default value is "application/json" if the type of `data` is
                `dict`. else, It gets set to "text/plain." You can specify the
                value you'd like to use to override this, too.
            headers:
                Headers to be sent if you need to specify additional headers.
                Beware that "Content-Type", and other values specified in
                `self.headers` will be overrided.

        Returns:
            a tuple with a format of `(data, status, res)`, where `data` is
            `dict`, `status` is `int` and `res` is either `HTTPResponse` or
            `HTTPError` object depending on what was the status code.
        """
        if method is None:
            method = "POST" if data else "GET"
        if content_type is None:
            if isinstance(data, dict):
                content_type = "application/json"
            else:
                content_type = "text/plain"
        if isinstance(data, dict):
            data = json.dumps(data)
        if isinstance(data, str):
            data = data.encode()
        headers.update({"Content-Type": content_type})
        headers.update(self.headers)

        url = urljoin(API_URL, endpoint)
        req = Request(url, data, headers, method=method)

        try:
            res = urlopen(req)
            try:
                status = res.status
            except AttributeError:
                status = res.getstatus()
        except HTTPError as e:
            res = e
            status = e.code

        rawdata = res.read()
        if rawdata:
            rtndata = json.loads(rawdata)
        else:
            rtndata = None

        return rtndata, status, res
