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

from queue import Queue

__all__ = ["EventHandler", "GeneratorEventHandler"]


class EventHandler:
    def __init__(self, client=None):
        self.client = None
        if client is not None:
            self.set_client(client)

    def set_client(self, client):
        self.client = client

    def handle(self, event, obj):
        raise NotImplementedError()


class GeneratorEventHandler(EventHandler):
    def __init__(self, client=None):
        super(GeneratorEventHandler, self).__init__(client)
        self.event_queue = Queue()

    def handle(self, event, obj):
        self.event_queue.put((event, obj))

    def event_generator(self):
        try:
            while not self.client.stop_flag.is_set():
                yield self.event_queue.get()
            return
        except KeyboardInterrupt:
            return
