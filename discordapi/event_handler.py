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

from .message import Message

from queue import Queue
from traceback import print_exc


class EventHandler:
    def __init__(self, client):
        self.client = client

    def handler(self, event, data, msg):
        raise NotImplementedError()


class GeneratorEventHandler(EventHandler):
    def __init__(self, client):
        super().__init__(client)
        self.event_queue = Queue()

    def handler(self, event, data, msg):
        if event in ["MESSAGE_CREATE", "MESSAGE_UPDATE"]:
            data = Message(data, self.client)
        self.event_queue.put((event, data))

    def event_generator(self):
        try:
            while not self.client.is_stop_requested.is_set():
                yield self.event_queue.get()
            return
        except KeyboardInterrupt:
            return

# TODO: Add a handler that uses decorator to register the handler
