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
    """
    Base Handler class.
    Subclass of this has to be used to handle events dispatched by Discord
    gateway.

    Attributes:
        client: The client which is using this handler right now.
    """
    def __init__(self):
        self.client = None

    def _set_client(self, client):
        """
        Setter for DiscordGateway Class to set `self.client` attribute value.
        It gets called whenever you assign this handler to DiscordGateway,
        DiscordClient or any other subclasses.
        """
        self.client = client

    def dispatch(self, type, event):
        """
        Dispatches the event to the appropriate function.
        The default behavior is to find the method in this class which has a
        name of "on_{event_type_lowercase}", call the method with `event` as
        its only argument, and run `on_error` function if an exception occurs
        and the function is present.
        """
        funcname = f"on_{type.lower()}"
        if not hasattr(self, funcname):
            return
        try:
            return getattr(self, funcname)(event)
        except Exception as e:
            if hasattr(self, "on_error"):
                return self.on_error(event, e)


class IterHandler(Handler):
    """
    Iterable handler which allows user to easily access dispatched events using
    iterator. This was intended to be used inside interactive shell, but you
    can use this handler to write a simple script without writing functions.

    Attributes:
        queue: A queue which will store dispatched events.
    """
    def __init__(self):
        super().__init__()
        self.queue = Queue()

    def dispatch(self, type, event):
        """
        Puts the dispatched event to `self.queue`. The format is (type, event).
        """
        self.queue.put((type, event))

    def iter(self):
        """
        Yields the dispatched event until the client disconnects.

        Returns:
            a tuple which has a following format: (type, event).
        """
        while not self.client.kill_event.is_set():
            yield self.queue.get()
