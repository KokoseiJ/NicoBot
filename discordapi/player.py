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
import logging
import subprocess
from threading import Event
from subprocess import PIPE, DEVNULL

__all__ = ["AudioSource", "FFMPEGAudioSource", "AudioPlayer",
           "SingleAudioPlayer", "QueuedAudioPlayer"]

SILENCE = b"\xf8\xff\xfe"

DELAY = 20 / 1000

logger = logging.getLogger("nicobot")


class AudioSource:
    """AudioSource providing the Opus packet to send to Voice server.
    """
    def prepare(self):
        """Preparation to do before the song plays.

        This method gets called before it starts playing. You can e.g. download
        the audio file, spawn a process, connect to remote server, etc etc.

        Whether to override this method or not is your choice.
        """
        pass

    def read(self):
        """Method that returns a packet of Opus audio stream to be sent.

        Return empty value (b'') if the audio stream has finished.

        Each packet contains around 20ms worth of data. If you're sending Opus
        data stored in Ogg container(which is also what FFMPEG uses), You can
        extract each packets from it and return it right away.

        This method should be implemented by the inherited class.
        """
        raise NotImplementedError()

    def cleanup(self):
        """Method to clean things after audio stops playing.

        This method gets called after the audio stops. You can e.g. remove the
        used audio file, kill the used process, etc etc.

        Whether to override this method or not is your choice.
        """
        pass


class FFMPEGAudioSource(AudioSource):
    """AudioSource that utilizes FFMPEG commandline tool to play audio.

    This class requires ffmpeg to be installed on the system.
    """
    def __init__(self, filename, inputargs=None, outputargs=None,
                 ffmpeg="ffmpeg"):
        """Initialize the ffmpeg settings.

        Args:
            filename:
                Input file to process. gets passed straight into -i.
            inputargs:
                Options to be used in input stream.
            outputargs:
                Options to be used in output stream.
            ffmpeg:
                directory to the binary. defaults to "ffmpeg".
        """
        self.filename = filename

        self.inputargs = [
            "-vn"
        ]
        if inputargs is not None:
            self.inputargs.extend(inputargs)

        self.outputargs = [
            "-f", "opus",
            "-ar", "48000",
            "-ac", "2",
            "-b:a", "96K",
            "-filter:a", "volume=0.5"
        ]
        if outputargs is not None:
            self.outputargs.extend(outputargs)

        self.FFMPEG = ffmpeg

        self.proc = None
        self.parser = None
        self.gen = None

    def prepare(self):
        """Starts FFMPEG process and initializes Ogg parser."""
        args = [self.FFMPEG] + self.inputargs + ["-i", self.filename] +\
            self.outputargs + ["-"]

        self.proc = subprocess.Popen(args, stdout=PIPE)#, stderr=DEVNULL)
        self.parser = OggParser(self.proc.stdout)
        self.gen = self.parser.packet_iter()

    def read(self):
        try:
            return next(self.gen)
        except StopIteration:
            return None

    def cleanup(self):
        self.proc.kill()


class AudioPlayer(StoppableThread):
    """Player to play AudioSource to given VoiceClient.

    This player is designed to be managed separately from the voice client.
    it will keep on running after the source finishes playing or client stops.
    you can also change which client to play to, if you want.

    This player inherits StoppableThread, will run on a separate thread, and is
    able to be stopped by calling .stop method.

    Attributes:
        client:
            DiscordVoiceClient to play to.
        source:
            Source to play with.
        callback:
            Function to be called after the source finishes.
        _resumed:
            Event indicating if the player has been paused or not.
        _ready:
            Event indicating if the player is ready to play.
        _sent_silence:
            bool indicating if the five frame of silence has been played after
            the player pauses playing.
        loop:
            Integer tracking how many packets have been sent so far, to
            determine when to send the next packet.
        start_time:
            Integer indicating when the transmission has started, to determine
            when to send the next packet.
    """
    def __init__(self, client=None, source=None, callback=None):
        """Initializes player.

        Args:
            client:
                Client to play to.
            source:
                Source to play with.
            callback:
                A function to be called after the song finishes playing. this
                function receives no arguments.
        """
        super(AudioPlayer, self).__init__()
        self.client = None
        self.source = None
        self.callback = None
        self.spoken = False

        self._resumed = Event()
        self._ready = Event()
        self._sent_silence = False

        self.loop = 0
        self.start_time = 0

        if client is not None:
            self.set_client(client)
        if source is not None:
            self.set_source(source)
        if callback is not None:
            self.set_callback(callback)
        
    def set_client(self, client):
        """Sets client. Also checks if client is in the right type."""
        if isinstance(client, DiscordVoiceClient):
            self.client = client
        else:
            raise TypeError("Invalid Voice Client Object.")

    def set_source(self, source):
        """Sets source. Also checks if source is in the right type."""
        if isinstance(source, AudioSource):
            self.source = source
        else:
            raise TypeError("Invalid Source Object.")

    def set_callback(self, callback):
        """Sets callback. Also checks if callback is in the right type."""
        if callable(callback):
            self.callback = callback
        else:
            raise TypeError("Invalid callback object.")

    def play(self, source=None):
        """Starts playing the source.

        It can set the source if provided.
        This method will refuse playing if either client or source is not set.
        """
        if source is not None:
            self.set_source(source)
        if self.client is None:
            raise RuntimeError("Client is not set.")
        if self.source is None:
            raise RuntimeError("Source is not set.")

        if self._ready.is_set():
            return

        self.source.prepare()
        self._prepare_play()
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
        self._resumed.set()

    def _prepare_play(self):
        """Initializes needed attributes to start playing."""
        self.loop = 0
        self._sent_silence = False
        self.spoken = False
        self.start_time = None
        self._resumed.set()

    def run(self):
        self._ready.wait()
        self.client.ready_to_run.wait()

        while not self.stop_flag.is_set():
            # Waits only 1 second so that stop_flag would still have effect
            # Check if client is ready
            if not self._ready.is_set():
                self._ready.wait(1)
                continue

            # Check if we're paused
            if not self._resumed.is_set():
                if not self._sent_silence:
                    # Sends 5 frame of silence as indicated in docs
                    for _ in range(5):
                        self._send_and_wait(SILENCE)
                    self._sent_silence = True
                self._resumed.wait(1)
                continue

            # Check if client is ready to play
            if not self.client.is_ready():
                if self.client.stop_flag.is_set():
                    # If the client is dead, try to determine a new client for
                    # the guild, and keep on playing to that client
                    # Do nothing if failed to do so
                    guild_id = self.client.server_id
                    gw_client = self.client.client
                    new_client = gw_client.voice_clients.get(guild_id)
                    if new_client is not None:
                        self.set_client(new_client)
                self.client.ready_to_run.wait(1)
                continue

            data = self.source.read()

            if not data:
                self._source_is_finished()
                continue

            if self._send_and_wait(data):
                break

    def _send_and_wait(self, data):
        if not self.spoken:
            self.client.speak(1)
            self.spoken = True
            self.start_time = time.perf_counter()
        self.client._send_voice(data)
        self.loop += 1

        wait_until = self.start_time + DELAY * (self.loop + 1)
        # Do this since it can result in negative integer
        delay = max(0, wait_until - time.perf_counter())
        time.sleep(delay)

    def _source_is_finished(self):
        self._ready.clear()
        if self.source is not None:
            self.source.cleanup()
        if self.callback is not None:
            self.callback()


class SingleAudioPlayer(AudioPlayer):
    """AudioPlayer that disconnects right after the source finishes."""
    def _source_is_finished(self):
        super(SingleAudioPlayer, self)._source_is_finished()
        self.client.disconnect()


class QueuedAudioPlayer(AudioPlayer):
    """AudioPlayer with audio queue implemented.

    player keeps on playing until the queue gets empty. .play method can be
    called again to resume playing.
    """
    def __init__(self, client=None, source=None, callback=None):
        super(QueuedAudioPlayer, self).__init__(client, source, callback)
        self.queue = []

    def set_source(self, source):
        if not isinstance(source, AudioSource):
            raise TypeError("Invalid Source Object.")

        self.queue.append(source)

    def add_to_queue(self, source):
        """Adds list of source to the queue. can be used with single object."""
        if hasattr(source, '__iter__'):
            for src in source:
                self.set_source(src)
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
        if self._ready.is_set():
            return

        self._update_source()
        self.source.prepare()
        self._prepare_play()
        self.client.speak(1)
        self._ready.set()

        if not self.is_alive():
            self.start()

    def _source_is_finished(self):
        super()._source_is_finished()
        if len(self.queue) > 0:
            self._update_source()
            self.source.prepare()
            self._prepare_play()
            self._ready.set()
