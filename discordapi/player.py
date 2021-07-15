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

from .ogg import OggParser
from .util import StoppableThread
from .voice import DiscordVoiceClient

import time
import subprocess
from queue import Queue
from threading import Event
from subprocess import PIPE, DEVNULL

__all__ = ["AudioSource", "FFMPEGAudioSource", "AudioPlayer",
           "SingleAudioPlayer", "QueuedAudioPlayer"]

SILENCE = b"\xf8\xff\xfe"

DELAY = 20 / 1000


class AudioSource:
    def prepare(self):
        return

    def read(self):
        raise NotImplementedError()

    def cleanup(self):
        return


class FFMPEGAudioSource(AudioSource):
    def __init__(self, filename, inputargs=[], outputargs=[], FFMPEG="ffmpeg"):
        self.filename = filename

        self.inputargs = outputargs

        self.outputargs = [
            "-f", "opus",
            "-ar", "48000",
            "-ac", "2",
            "-b:a", "96K"
        ]
        if outputargs:
            self.outputargs.extend(outputargs)

        self.FFMPEG = FFMPEG

        self.proc = None
        self.parser = None
        self.gen = None

    def prepare(self):
        args = [self.FFMPEG] + self.inputargs + ["-i", self.filename] +\
                self.outputargs + ["-"]

        self.proc = subprocess.Popen(args, stdout=PIPE, stderr=DEVNULL)
        self.parser = OggParser(self.proc.stdout)
        self.gen = self.parser.packet_iter()

    def read(self):
        try:
            return next(self.gen)
        except StopIteration:
            return None


class AudioPlayer(StoppableThread):
    def __init__(self, client=None, source=None, callback=None):
        super(AudioPlayer, self).__init__()
        self.client = None
        self.source = None
        self.callback = None

        self._resumed = Event()
        self._ready = Event()

        self.loop = 0
        self.start_time = 0

        if client is not None:
            self.set_client(client)
        if source is not None:
            self.set_source(source)
        if callback is not None:
            self.set_callback(callback)
        
    def set_client(self, client):
        if isinstance(client, DiscordVoiceClient):
            self.client = client
        else:
            raise TypeError("Invalid Voice Client Object.")

    def set_source(self, source):
        if isinstance(source, AudioSource):
            self.source = source
        else:
            raise TypeError("Invalid Source Object.")

    def set_callback(self, callback):
        if callable(callback):
            self.callback = callback
        else:
            raise TypeError("Invalid callback object.")

    def play(self, source=None):
        if source is not None:
            self.set_source(source)
        if self.client is None:
            raise RuntimeError("Client is not set.")
        if self.source is None:
            raise RuntimeError("Source is not set.")

        self._prepare_play()
        self.client.speak(1)
        self._ready.set()

        if not self.is_alive():
            self.start()

    def stop(self):
        self._source_is_finished()
        self.client.speak(0)

    def pause(self):
        self._resumed.clear()
        self.client.speak(0)

    def resume(self):
        self._prepare_play()
        self.client.speak(1)
        self._resumed.set()

    def _prepare_play(self):
        self.source.prepare()
        self.start_time = time.perf_counter()
        self.loop = 0
        self._resumed.set()

    def run(self):
        self._ready.wait()
        ready_to_run = self.client.ready_to_run

        while ready_to_run.is_set() and not self.stop_flag.is_set():
            if not self._ready.is_set():
                self._ready.wait(1)
                continue

            if not self._resumed.is_set():
                for _ in range(5):
                    self._send_and_wait(SILENCE)
                self._resumed.wait()
                continue

            data = self.source.read()

            if not data:
                self._source_is_finished()
                continue

            if self._send_and_wait(data):
                break

    def _send_and_wait(self, data):
        self.client._send_voice(data)
        self.loop += 1

        wait_until = self.start_time + DELAY * self.loop
        delay = max(0, wait_until - time.perf_counter())
            
        if self.stop_flag.wait(delay):
            return True

    def _source_is_finished(self):
        self._ready.clear()
        self.source.cleanup()
        self.callback()


class SingleAudioPlayer(AudioPlayer):
    def _source_is_finished(self):
        super(SingleAudioPlayer, self)._source_is_finished()
        self.client.disconnect()


class QueuedAudioPlayer(AudioPlayer):
    def __init__(self, client=None, source=None, callback=None):
        super(QueuedAudioPlayer, self).__init__(client, source, callback)
        self.queue = []

    def set_source(self, source):
        if not isinstance(source, AudioSource):
            raise TypeError("Invalid Source Object.")

        self.queue.append(source)

    def add_to_queue(self, source):
        if hasattr(source, '__iter__'):
            for src in source:
                self.source(src)
        else:
            self.set_source(source)

    def _update_source(self):
        if len(self.queue) == 0:
            raise RuntimeError("Queue is empty.")
        self.source = self.queue.pop(0)

    def play(self, source=None):
        if source is not None:
            self.set_source(source)
        if self.client is None:
            raise RuntimeError("Client is not set.")
        
        self._update_source()
        self._prepare_play()
        self.client.speak(1)
        self._ready.set()

        if not self.is_alive():
            self.start()

    def _source_is_finished(self):
        self._ready.clear()
        self.source.cleanup()
        self.callback()
        if len(self.queue) > 0:
            self._update_source()
            self._prepare_play()
            self._ready.set()
