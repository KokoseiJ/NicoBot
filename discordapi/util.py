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

from .const import EMPTY
from .file import File

import os
import json
from select import select
from threading import Thread, Event

__all__ = []


class StoppableThread(Thread):
    def __init__(self, *args, **kwargs):
        super(StoppableThread, self).__init__(*args, **kwargs)
        self.stop_flag = Event()

    def stop(self):
        self.stop_flag.set()


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
        if self.is_set():
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


def clear_postdata(data):
    """checks for postdata and remove the key if the value is EMPTY."""
    return {key: value for key, value in data.items() if value is not EMPTY}


def filter_dict(data, keys):
    return {key: value for key, value in data.items() if key in keys}


def get_formdata(data, boundary_prefix=None):
    if boundary_prefix is None:
        boundary_prefix = "VOCALOIDIA-"

    randhex = os.urandom(8).hex()
    boundary = f"{boundary_prefix}{randhex}"

    content_type = f'multipart/form-data;boundary="{boundary}"'

    body = bytes()

    for key, value in data.items():
        body += f"--{boundary}\n".encode()
        body += f'Content-Disposition: form-data; name="{key}"'.encode()

        if isinstance(value, dict):
            value = json.dumps(value).encode()
        elif isinstance(value, File):
            name = value.get_name()
            value = value.read()
            body += f'; filename="{name}"\n'.encode()
            body += b"Content-Type: application/octet-stream"

        body += b"\n\n"
        body += value if isinstance(value, bytes) else value.encode()
        body += b"\n"
    body += f"--{boundary}--\n".encode()

    return content_type, body
