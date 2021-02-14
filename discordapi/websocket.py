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

import os
import json

from select import select
from websocket import WebSocket
from threading import Thread, Lock


class SelectableEvent:
    """
    Event class that has fileno implemented, so that it would work with
    `select` syscall.
    This works by writing a byte to a pipe when setting the event, and reading
    it when clearing it. so that It could be detected with `select` syscall.
    from https://lat.sk/2015/02/multiple-event-waiting-python-3/

    Attributes:
        _read_fd:
            pipe file descriptor.
        _write_fd:
            same as _read_fd.
    """
    def __init__(self):
        """
        Opens the pipe.
        """
        self._read_fd, self._write_fd = os.pipe()

    def wait(self, timeout=None):
        """
        Use `select` syscall to check if the flag has been set.
        """
        readable, _, _ = select((self._read_fd,), (), (), timeout)
        return self._read_fd in readable

    def is_set(self):
        """
        Run `self.wait` method with timeout set to 0 so that it won't block.
        """
        return self.wait(0)

    def clear(self):
        """
        Reads a byte from the pipe to reset.
        """
        if self.isSet():
            os.read(self._read_fd, 1)

    def set(self):
        """
        Write a byte to the pipe to set the flag.
        """
        if not self.is_set():
            os.write(self._write_fd, b"1")

    def fileno(self):
        """
        Returns the file descriptor, so that it could be used with `select`.
        """
        return self._read_fd

    def __del__(self):
        """
        Closes the opened pipe.
        """
        os.close(self._read_fd)
        os.close(self._write_fd)


class StoppableThread(Thread):
    """
    Thread that has stop method implemented.
    Refer to threading.Thread for more information.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._is_stopped = SelectableEvent()

    def stop(self):
        """
        Stops the thread.
        """
        self._is_stopped.set()

    def stopped(self):
        """
        Checks if _is_stopped flag is set.
        """
        return self._is_stopped.is_set()


class WebSocketClient:
    """
    Websocket client that is used when connecting to Discord gateway.

    Attributes:
        url: URL address of target websocket server.
        sock: Internal socket.
        connection_thread: Thread that runs `self.connect`.
        heartbeat_thread: Thread that handles Heartbeat.
        kill_event: Event that determines if thread should be killed or not.
        send_lock: Lock object that ensures threadsafety while sending message.
    """
    def __init__(self, url):
        """
        Initializes WebSocketClient.

        Args:
            url:
                URL address of target websocket server.
        """
        self.url = url
        self.sock = None

        self.connection_thread = None
        self.heartbeat_thread = None

        self.kill_event = SelectableEvent()
        self.send_lock = Lock()

    def _handle(self, sock, handler):
        """
        Handler that dispatches Websocket events.

        Args:
            sock:
                WebSocket object that has events to be received.
            handler:
                Handler which will handle events.
        """
        if not sock.connected:
            return
        while True:
            readable, _, _ = select((sock.sock,), (), ())
            if readable:
                data = sock.recv()
                if not data:
                    return
                data = json.loads(data)
                handler(data)

    def _send(self, data):
        """
        Wrapper of `self.sock.send` method which applies thread lock to ensure
        threadsafety.

        Args:
            data:
                str to be passed to `self.sock.send` method.

        Returns:
            Length of sent bytes.
        """
        self.send_lock.acquire()
        rtnval = self.sock.send(data)
        self.send_lock.release()
        return rtnval

    def clean(self):
        """
        Cleans up the attributes after closing the socket.
        """
        if self.heartbeat_thread:
            self.heartbeat_thread.stop()
            self.heartbeat_thread.join()
            self.heartbeat_thread = None
        self.sock = None
        if not self.send_lock.acquire(False):
            self.send_lock.release()

    def close(self, *args, **kwargs):
        """
        Wrapper of `self.sock.close` method. To ensure the thread to die
        without attempting to reconnect, please use this method instead of
        `self.sock.close`.

        Args:
            reconnect:
                bool that decides if client should attempt to reconnect.
        """
        if self.sock is None:
            raise RuntimeError("Websocket has not been connected yet!")
        self.sock.close(*args, **kwargs)
        reconn = kwargs.get("reconnect", False)
        if not reconn:
            self.kill_event.set()

    def connect(self):
        """
        Connects to the websocket server.
        This method will also try to reconnect to the server after connection
        has been dropped, unless it was closed by user using `self.close`
        method.
        """
        if self.sock is not None:
            raise RuntimeError("Websocket has been already opened.")

        connected = False
        while not self.kill_event.is_set():
            self.sock = WebSocket()
            self.sock.connect(self.url)
            if not connected:
                self.on_connect(self.sock)
                connected = True
            else:
                self.on_reconnect(self.sock)
            self._handle(self.sock, self.on_message)
            self.clean()

    def connect_threaded(self):
        """
        Starts the new thread that runs `self.connect` method.

        Returns:
            Thread object which connect method is running.
        """

        self.connection_thread = StoppableThread(
            target=self.connect,
            name="run_thread"
        )
        self.connection_thread.start()
        return self.connection_thread

    def run_heartbeat(self):
        """
        Starts the new thread that runs `self.hearbeat` method.

        Returns:
            Thread object which heartbeat method is running.
        """
        self.heartbeat_thread = StoppableThread(
            target=self.heartbeat,
            name="heatbeat_thread"
        )
        self.heartbeat_thread.start()
        return self.heartbeat_thread

    def send(self, data):
        """
        Wrapper of `self._send` method, which will convert `dict` to JSON
        string.
        """
        if self.sock is None or not self.sock.connected:
            raise RuntimeError("Websocket has not been connected yet!")
        if isinstance(data, dict):
            data = json.dumps(data)
        return self._send(data)

    def on_connect(self, ws):
        """
        Function to be called when the connection gets established.
        You have to implement this method by yourself.

        Args:
            ws:
                Websocket object. You can either send or recieve using this
                object since dispatcher will start running after this function.
        """
        raise NotImplementedError()

    def on_reconnect(self, ws):
        """
        Function to be called when the client tries to reconnect to the server.
        You have to implement this method by yourself.

        Args:
            ws:
                Websocket object. You can either send or recieve using this
                object since dispatcher will start running after this function.
        """
        raise NotImplementedError()

    def on_message(self, data):
        """
        Function to be called when it recevies the data from websocket.
        You have to implement this method by yourself.

        Args:
            data:
                `dict` object which has the data returned from the server.
        """
        raise NotImplementedError()

    def heatbeat(self):
        """
        Heartbeat method.
        In order to be closed properly, this method should check
        `self.heartbeat_thread.stopped` method's result regularly, and be
        stopped when it returns `True`.
        You have to implement this method by yourself.
        """
        raise NotImplementedError()
