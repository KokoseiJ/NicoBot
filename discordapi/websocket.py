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
from .util import StoppableThread, SelectableEvent

import json
import time
import random
import select
import logging
from ssl import SSLError
from websocket import WebSocket, WebSocketConnectionClosedException

__all__ = []

logger = logging.getLogger(LIB_NAME)


class WebSocketThread(StoppableThread):
    """Base class for running WebSocket connection.

    It has .do_heartbeat, .init_connection, .cleanup method to be overriden by
    inherited client, for defining desired behaviour depending on clients.

    This class inherits from Thread, and is running as a separate thread.
    To start the client, you have to invoke .start method as you would with
    typical threads.

    Attributes:
        url:
            URL of the gateway for this client to connect to.
        handler:
            Handler to be called when the event has been received. It should
            recieve a single argument with type of dict.
        ready_to_run:
            Event object indicating if the event is ready to be used. This
            event must be set manually by the inherited class.
        _sock:
            internal WebSocket object to be used to communicate with gateway.
        heartbeat_thread:
            Thread where .do_heartbeat method runs. This thread runs throughout
            the lifetime of this thread, so .do_heartbeat should be written
            with continuability in mind.
        init_thread:
            Thread where init_thread method runs. It runs in thread so that
            ._event_loop method could run parellelly. This thread is expected
            to run quick and quit shortly after.
    """
    def __init__(self, url, handler, name):
        """
        Args:
            url:
                same as .url attribute
            handler:
                same as .handler attribute
            name:
                same as handler argument in threading.Thread
        """
        super(WebSocketThread, self).__init__()

        self.url = url
        self.handler = handler
        self.ready_to_run = SelectableEvent()
        self.name = str(name)
        
        self._sock = None

        self.heartbeat_thread = None
        self.init_thread = None

    def run(self):
        """Start the heartbeat and run _event_loop in a loop until .stop calls.

        heartbeat_thread, init_thread gets created in this method, as well as
        .cleanup method which gets called after the socket disconnects.

        Since the connection restarts after the socket has been disconnected,
        if a problem occurs from eg. heartbeat thread or init thread, you can
        call ._sock.stop method to stop the socket and reconnect.
        """
        self._sock = WebSocket(
            enable_multithread=True,
            skip_utf8_validation=True
        )
        self.run_heartbeat()

        while True:
            logger.debug("Connecting to Gateway...")
            try:
                self._sock.connect(self.url)
            except Exception:
                logger.exception("Failed to connect to Gateway.")

            self.run_init_connection()

            self._event_loop()

            logger.warning("Gateway connection is lost!")

            self.ready_to_run.clear()
            try:
                self.cleanup()
            except Exception:
                logger.exception("Exception occured while cleaning up.")

            if self.stop_flag.is_set():
                break
            else:
                time.sleep(random.randint(1, 5))

        logger.debug("Stopping thread...")

        self.heartbeat_thread.stop()

    def run_heartbeat(self):
        logger.debug("Starting heartbeat thread.")
        self.heartbeat_thread = StoppableThread(
            target=self.do_heartbeat,
            name=f"{self.name}_heartbeat"
        )
        self.heartbeat_thread.start()

    def run_init_connection(self):
        logger.debug("Starting init thread.")
        self.init_thread = StoppableThread(
            target=self.init_connection,
            name=f"{self.name}_init"
        )
        self.init_thread.start()

    def _event_loop(self):
        """Receives from _socket, parses it to JSON and passes it to handler.
        """
        while self._sock.connected:
            rl, _, _ = select.select((self._sock.sock,), (), ())
            if self._sock.sock not in rl:
                continue
            try:
                data = self._sock.recv()
                if not data:
                    continue
                parsed_data = json.loads(data)
            except json.JSONDecodeError:
                logger.error(f"Gateway returned invalid JSON data:\n{data}")
            except WebSocketConnectionClosedException:
                break
            except Exception:
                logger.exception(
                    "Exception occured while receiving data from the gateway.")

            try:
                logger.debug("Received " + data)
                self.handler(parsed_data)
            except Exception:
                logger.exception(
                    "Exception occured while running handler function.")

    def send(self, data):
        """serializes data to json if dict, and send it through the socket.

        I strongly encourage you to use this method instead of _sock.send, 
        because this method is meant to solve the SSLError caused by ssl module
        by catching the exception and running the method recursively.
        """
        if isinstance(data, dict):
            data = json.dumps(data)

        try:
            logger.debug("Sent " + data)
            return self._sock.send(data)
        except SSLError:
            logger.exception("SSLError while sending data! retrying...")
            return self.send(data)

    def is_ready(self):
        return self.ready_to_run.is_set()

    def reconnect(self, status=1006, *args, **kwargs):
        self._sock.close(status=1006, *args, **kwargs)

    def stop(self, status=1000):
        """Stops the gateway connection.

        This client cannot be started after this method has been called, since
        .start method in Thread object can only be called once per instances.
        if you have to restart the client, you have to create a new instance.
        """
        super(WebSocketThread, self).stop()
        self._sock.close(status=status)

    def init_connection(self):
        """Method to be run when websocket connection establishes.

        This method is expected to run shortly, if a problem occurs during the
        procedure, run .reconnect method which will reestablish the connection.

        This method should be implemented by the inherited client.
        """
        raise NotImplementedError()

    def do_heartbeat(self):
        """Method to be run when websocket connection establishes.

        This method runs throughout the main thread's lifetime, so you should
        consider that while overriding the method.

        This method should be implemented by the inherited class.
        """
        raise NotImplementedError()

    def cleanup(self):
        """Method to be called after the client disconnects.

        This method exists to reset the attributes when needed. if not, you can
        just leave this method as is.

        whether to override this method or not is your choice.
        """
        pass
