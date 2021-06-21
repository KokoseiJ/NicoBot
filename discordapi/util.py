from .const import EMPTY

import os
from select import select
from threading import Thread

__all__ = []


class StoppableThread(Thread):
    def __init__(self, *args, **kwargs):
        super(StoppableThread, self).__init__(*args, **kwargs)
        self.stop_flag = SelectableEvent()

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
    return {
        key: value for key, value in data.items() if value is not EMPTY
    }
