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

from .const import LIB_NAME

import time
import logging

__all__ = ["RateLimitHandler"]

logger = logging.getLogger(LIB_NAME)


class RateLimitHandler:
    def __init__(self):
        self.bucket_map = {}
        self.limit_list = {}
        self.global_limit = None
        # Locks are removed since most of the major python implements have
        # thread-safe dict implementation.

    def register_bucket(self, route, bucket):
        route = self.uniformize_route(route)
        self.bucket_map.update({route: bucket})

    def uniformize_route(self, route):
        return route if route.startswith("/") else f"/{route}"

    def get_route(self, route):
        route = self.uniformize_route(route)
        if route in self.bucket_map:
            return self.bucket_map.get(route)

    def update(self, route, data):
        bucket = data.get("x-ratelimit-bucket")

        if bucket is not None:
            self.register_bucket(route, bucket)

        self.limit_list.update({bucket: data})

        if data.get("x-ratelimit-global"):
            self.global_limit = float(data.get("x-ratelimit-reset"))
            logger.warning(
                "You're globally rate limited until %d!", self.global_limit)

    def check_global(self):
        if self.global_limit:
            self.wait_until(self.global_limit)
            self.global_limit = None

    def get_data(self, route):
        data = self.limit_list.get(route)

        if data and time.time() > float(data.get("x-ratelimit-reset")):
            self.limit_list.update({route: None})
            return None

        return data

    def check(self, route):
        self.check_global()

        route = self.get_route(route)
        data = self.get_data(route)

        if data and data.get("x-ratelimit-remaining") == "0":
            reset_time = float(data.get("x-ratelimit-reset"))
            logger.warning(
                "You're rate limited in %s until %f!", route, reset_time)
            self.wait_until(reset_time)
            self.limit_list.update({route: None})

    def wait_until(self, until):
        time.sleep(max(until - time.time(), 0))
