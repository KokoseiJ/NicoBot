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
from .exception import DiscordHTTPError
from .channel import get_channel
from .const import LIB_NAME, LIB_URL, LIB_VER, API_URL

import json
import logging
from urllib.parse import urljoin
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from json.decoder import JSONDecodeError

logger = logging.getLogger(LIB_NAME)


class DiscordClient(DiscordGateway):
    def __init__(self, token, intents=None, event_handler=None):
        super().__init__(token, intents, event_handler)

        self.headers = {
            "User-Agent": f"{LIB_NAME} ({LIB_URL}, {LIB_VER})",
            "authorization": f"Bot {self.token}"
        }

    def get_channel(self, id):
        data, status = self._request(f"channels/{id}")
        return get_channel(data, self)

    def _request(self, endpoint, method="GET", data=None, is_json=True,
                 headers=None, throw=True):
        if isinstance(data, dict):
            data = json.dumps(data).encode()
        elif isinstance(data, str):
            data = data.encode()

        url = urljoin(API_URL, endpoint)

        _headers = self.headers.copy()
        if data is not None and is_json:
            _headers.update({"Content-Type": "application/json"})
        if headers is not None and isinstance(headers, dict):
            _headers.update(headers)

        logger.debug(f"Sending {method} request to {url}")
        req = Request(url, data, _headers, method=method)
        try:
            res = urlopen(req)
            try:
                status = res.getstatus()
            except AttributeError:
                status = res.status
            raised = False
        except HTTPError as e:
            res = e
            status = e.code
            raised = True

        rawdata = res.read()
        try:
            data = json.loads(rawdata)
        except JSONDecodeError:
            data = rawdata.decode()

        if raised and throw:
            raise DiscordHTTPError(res, data) from res
        return data, status
