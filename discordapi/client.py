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
    def __init__(self, token, handler, intents=INTENTS_DEFAULT):
        super().__init__(token, handler, intents)
        self.headers = {
            "User-Agent": f"{LIB_NAME} ({LIB_URL}, {LIB_VER})",
            "Authorization": f"Bot {self.token}"
        }

    def _request(self, endpoint, data=None, method=None, content_type=None,
                 headers={}):
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
        print(data)
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
