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

from queue import Queue
from threading import Thread

__all__ = ["EventHandler", "GeneratorEventHandler"]


class EventHandler:
    """Base client for EventHandler.

    Attributes:
        self.client
    """
    def __init__(self, client=None):
        self.client = None
        if client is not None:
            self.set_client(client)

    def set_client(self, client):
        """Sets client to be used.

        Required to provide client-side interface and contexts to handlers.
        """
        from .gateway import DiscordGateway
        if not isinstance(client, DiscordGateway):
            raise TypeError("client should be DiscordGateway, "
                            f"not '{type(client)}'")
        self.client = client

    def handle(self, event, obj):
        """Handler function to handle the event.

        This method handles the event fired by the Gateway.
        Since this runs on a main client thread, running a time-consuming job
        will block other events from reaching the client, stopping the bot from
        functioning. Please start another thread for those jobs.

        This method should be implemented by the inherited class.

        Args:
            event:
                str indicating the type of this event. comes in ALL_CAPS.
            obj:
                Corresponding type of object for the event.
                Possible types are: Channel/Guild/Member/Message/dict.
                Check DiscordGateway._event_parser method to see how things
                are handled.
        """
        raise NotImplementedError()


class GeneratorEventHandler(EventHandler):
    """Handler to be used within terminal, or with a simple bot.

    This handler provides a new way to handle events- by using a generator.
    By iterating through .event_generator method with for loop, You can receive
    events without declaring additional functions, which is suitable for simple
    usages.

    Attributes:
        self.event_queue:
            Queue object storing events.
    """
    def __init__(self, client=None):
        super(GeneratorEventHandler, self).__init__(client)
        self.event_queue = Queue()

    def handle(self, event, obj):
        self.event_queue.put((event, obj))

    def event_generator(self):
        """Generator yielding events.

        Yielded data will be in a tuple of (event, obj)- where event is the
        type of the object and obj is the object itself. Same as .handle args.

        This generator could be used like this:
        ```
        for event, obj in handler.event_generator():
            print(f"{event}: {obj}")
        ```
        or, in the interpreter: like this:
        ```
        >>> gen = handler.event_generator()
        >>> event, obj = next(gen)
        >>> print(f"{event}: {obj}")
        >>> # Rinse and repeat 
        ```

        Additionally, This generator silences KeyboardInterrupt exception.
        """
        try:
            while not self.client.stop_flag.is_set():
                yield self.event_queue.get()
            return
        except KeyboardInterrupt:
            return


class MethodEventHandler(EventHandler):
    """Handler to handle methods with defined methods.

    This handler calls .on_{lowercased event type} method when event issues.
    e.g. self.on_message_create method gets called when MESSAGE_CREATE fires.
    If the corresponding method has not defined, It does nothing.

    The arguments handlers will receive is the same as .handle method.

    Since this runs on a main client thread, running a time-consuming job
    will block other events from reaching the client, stopping the bot from
    functioning. Please start another thread for those jobs.

    No method other than .handle comes predefined, You have to either
    inherit this method or assign functions as attributes to use this.
    """
    def handle(self, event, obj):
        method_name = f"on_{event.lower()}"
        handler = getattr(self, method_name, None)
        if handler is not None:
            handler(event, obj)


class DecoratorEventHandler(EventHandler):
    """Handler to assign functions per events with decorator.

    It lets you assign individual handlers per events using decorator, similar
    to how other libraries such as Discord.py and Telethon works.

    You can use @handler.on("event_name") to assign the handler.

    function to be assigned should receive a single arguments- the object
    returned from the gateway. Additional context such as client object should
    be provided separately.
    being provided as a purpose of giving context.

    Other than decorator, This handler behaves similar to MethodEventHandler.
    """
    def handle(self, event, obj):
        method_name = f"on_{event.lower()}"
        handler = getattr(self, method_name, None)
        if handler is not None:
            handler(obj, self)

    def on(self, event):
        def decorator(func):
            method_name = f"on_{event.lower()}"
            setattr(self, method_name, func)
            return func
        return decorator


class ThreadedMethodEventHandler(MethodEventHandler):
    """Handler that starts thread automatically per every events.

    Since handler runs on a main client thread, time-consuming actions will
    block other events from reaching, stopping the bot from functioning. this
    handler will counter that problem by starting a new thread for every events
    being fired.

    This is a basic implementation with no limits or safety measures being
    placed whatsoever, and could be critical to performance. I recommend
    implementing your own handler with appropriate safety measures in place.
    """
    def handle(self, event, obj):
        method_name = f"on_{event.lower()}"
        handler = getattr(self, method_name, None)
        if handler is not None:
            Thread(target=handler, args=(event, obj)).start()


class ThreadedDecoratorEventHandler(DecoratorEventHandler):
    """Same as ThreadedMethodEventHandler, but decorator version.

    Refer to ThreadMethodEventHandler for details, those cautions apply here
    too.
    """
    def handle(self, event, obj):
        method_name = f"on_{event.lower()}"
        handler = getattr(self, method_name, None)
        if handler is not None:
            Thread(target=handler, args=(obj,)).start()

    def on(self, event):
        def decorator(func):
            method_name = f"on_{event.lower()}"
            setattr(self, method_name, func)
            return func
        return decorator
