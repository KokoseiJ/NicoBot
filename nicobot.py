from discordapi import DiscordClient, CommandError, CommandManager, \
                       ThreadedCommandEventHandler, QueuedAudioPlayer, \
                       FFMPEGAudioSource
from niconico import NicoPlayer
import os
import re
import sys
import random
import logging
from logging import StreamHandler

logger = logging.getLogger("nicobot")
handler = StreamHandler(sys.stdout)
fmt = logging.Formatter("[%(levelname)s]|%(asctime)s|%(threadName)s|"
                        "%(funcName)s|: %(message)s")
handler.setFormatter(fmt)
logger.addHandler(handler)
logger.setLevel("INFO")
handler.setLevel("INFO")

id_ = os.environ.get("ID")
pw = os.environ.get("PW")

player = NicoPlayer()
if id_ and pw:
    player.login(id_, pw)

id_check = re.compile("[a-z]{2}[0-9]+")
mylist_check = re.compile(
    "(?:https?\:\/\/)?(?:www.)?nicovideo.jp\/"
    "(?:user\/[0-9]+\/)?mylist\/([0-9]+)"
)
watch_check = re.compile(
    "(?:https?\:\/\/)?(?:www.)?nicovideo.jp\/watch\/([a-z]{2}?[0-9]+)"
)


def check_type(arg):
    id_match = id_check.match(arg)
    if id_match:
        return 1, arg
    watch_match = watch_check.match(arg)
    if watch_match:
        return 1, watch_match.groups()[0]
    mylist_match = mylist_check.match(arg)
    if mylist_match:
        return 2, mylist_match.groups()[0]
    else:
        return 0, arg


class NicoAudioSource(FFMPEGAudioSource):
    def __init__(self, video, *args, **kwargs):
        super().__init__(None, *args, **kwargs)
        self.video = video
        self.session = None

    def prepare(self):
        self.session = player.play(self.video.id)
        self.session.prepare("best", "worst")
        self.filename = self.session.start()
        super().prepare()

    def cleanup(self):
        self.session.stop_flag.set()
        super().cleanup()


class NicoBot(CommandManager):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.channels = dict()
        self.clients = dict()
        self.players = dict()

    def execute_cmd(self, cmdinput, message):
        if message.guild is None:
            return
        self.channels.update({message.guild.id: message.channel.id})

        return super().execute_cmd(cmdinput, message)

    def join(self, cmd, message):
        user_id = message.author.id
        channel = message.guild.voice_state.get(user_id)

        if channel is None:
            raise CommandError(
                cmd,
                "Failed to connect!",
                "You are not connected to VC. please reconnect and try again."
            )

        vc = channel.connect()
        player = QueuedAudioPlayer(vc)

        self.clients.update({message.guild.id: vc})
        self.players.update({message.guild.id: player})

        return f"Successfully joined {channel.name}!"

    def play(self, cmd, message):
        music_player = self.players.get(message.guild.id)
        if music_player is None:
            raise CommandError(
                cmd,
                "Failed to play!",
                "I am not connected to VC!"
            )

        type_, val = check_type(cmd)
        if type_ == 2:
            mylist = player.get_mylist(val)
            videos = mylist.items
        elif type_ == 0:
            videos = player.search(val, _limit=1)[:1]
            if len(videos) == 0:
                raise CommandError(
                    cmd,
                    "Video not found!",
                    "Video was not found. please try different keywords."
                )
        elif type_ == 1:
            videos = [player.get_thumb_info(val)]

        sources = [NicoAudioSource(video) for video in videos]

        if len(sources) == 1:
            yield f"Added {videos[0].title} to the queue!"
        else:
            yield f"Added mylist {mylist.name} to the queue!"

        music_player.add_to_queue(sources)
        music_player.play()

    def stop(self, cmd, message):
        music_player = self.players.get(message.guild.id)
        if music_player is None:
            raise CommandError(
                cmd,
                "Failed to play!",
                "I am not connected to VC!"
            )

        music_player.queue.clear()
        music_player.stop()

        return "Stopped playing!"

    def skip(self, cmd, message):
        music_player = self.players.get(message.guild.id)
        if music_player is None:
            raise CommandError(
                cmd,
                "Failed to play!",
                "I am not connected to VC!"
            )

        title = music_player.source.video.title

        music_player.stop()

        return f"Skipped {title}!"

    def shuffle(self, cmd, message):
        music_player = self.players.get(message.guild.id)
        if music_player is None:
            raise CommandError(
                cmd,
                "Failed to play!",
                "I am not connected to VC!"
            )

        random.shuffle(music_player.queue)

        return "Shuffled the queue!"

    def pause(self, cmd, message):
        music_player = self.players.get(message.guild.id)
        if music_player is None:
            raise CommandError(
                cmd,
                "Failed to play!",
                "I am not connected to VC!"
            )

        music_player.pause()
        return "Paused!"

    def resume(self, cmd, message):
        music_player = self.players.get(message.guild.id)
        if music_player is None:
            raise CommandError(
                cmd,
                "Failed to play!",
                "I am not connected to VC!"
            )

        music_player.resume()
        return "Resumed!"

    def leave(self, cmd, message):
        music_player = self.players.get(message.guild.id)
        client = self.clients.get(message.guild.id)
        if music_player is None:
            raise CommandError(
                cmd,
                "Failed to play!",
                "I am not connected to VC!"
            )

        music_player.stop()
        music_player.stop_flag.set()
        client.disconnect()
        self.players[message.guild.id] = None
        self.clients[message.guild.id] = None

        return "Successfully disconnected!"


handler = ThreadedCommandEventHandler(NicoBot, "?")

client = DiscordClient(
    open("token").read(),
    handler=handler
)

try:
    client.start()
    client.ready_to_run.wait()
    client.update_presence(activities=[{'type': 2, 'name': 'Orangestar'}])
    client.join()
except KeyboardInterrupt:
    client.stop()
    client.join()
