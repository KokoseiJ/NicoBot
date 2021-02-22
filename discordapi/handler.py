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

__all__ = ["Handler", "IterHandler"]

from queue import Queue


class Handler:
    def __init__(self):
        self.client = None

    def _set_client(self, client):
        self.client = client

    def dispatch(self, type, event):
        funcname = f"on_{type.lower()}"
        if not hasattr(self, funcname):
            return
        try:
            return getattr(self, funcname)(event)
        except Exception as e:
            if hasattr(self, "on_error"):
                return self.on_error(event, e)


class IterHandler(Handler):
    def __init__(self):
        super().__init__()
        self.queue = Queue()

    def dispatch(self, type, event):
        self.queue.put((type, event))

    def iter(self):
        while not self.client.kill_event.is_set():
            yield self.queue.get()
