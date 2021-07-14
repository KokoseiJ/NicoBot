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

from .const import LIB_NAME

import time
import logging
from threading import Lock

__all__ = ["RateLimitHandler"]

logger = logging.getLogger(LIB_NAME)


class RateLimitHandler:
    def __init__(self):
        self.bucket_map = {}
        self.limit_list = {}
        self.bucket_map_lock = Lock()
        self.limit_list_lock = Lock()

    def is_in_bucket_map(self, route):
        return route in self.bucket_map

    def register_bucket(self, route, bucket):
        with self.bucket_map_lock:
            self.bucket_map[route] = bucket

        with self.limit_list_lock:
            limit = self.limit_list.get(route)
            if limit is not None:
                del self.limit_list[route]
                self.limit_list[bucket] = limit

        logger.info(f"Registered {bucket} to {route}")

    def set_limit(self, route, limit):
        if route in self.bucket_map:
            route = self.bucket_map[route]

        logger.warning(f"You are being rate limited in {route} until {limit}!")

        with self.limit_list_lock:
            self.limit_list[route] = limit

    def check(self, route):
        if route in self.bucket_map:
            route = self.bucket_map[route]
        
        limit = self.limit_list.get(route)
        if limit:
            self._wait(limit)
            self._reset_limit(route, limit)

        global_limit = self.limit_list.get("global")
        if global_limit:
            self._wait(global_limit)
            self._reset_limit("global", global_limit)

        return False  

    def _wait(self, limit):
        now = time.time()
        if now < limit:
            time.sleep(limit - now)

    def _reset_limit(self, route, expected_value):
        with self.limit_list_lock:
            if self.limit_list.get(route) == expected_value:
                del self.limit_list[route]
