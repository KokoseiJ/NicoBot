from discordapi.slash import (
    SlashCommand, SubCommand, String, DiscordInteractionClient,
    InteractionEventHandler, SlashCommandManager
)

from discordapi import (
    QueuedAudioPlayer, FFMPEGAudioSource, Embed, ThreadedMethodEventHandler
)
from niconico import NicoPlayer

import os
import sys
import logging

from colorlog import ColoredFormatter
from logging import StreamHandler, FileHandler


logger = logging.getLogger("nicobot")
logger.setLevel("DEBUG")
fmt = ColoredFormatter("%(log_color)s[%(levelname)s]|%(asctime)s|"
                       "%(threadName)s|%(funcName)s|: %(message)s")
handler = StreamHandler(sys.stdout)
handler.setFormatter(fmt)
handler.setLevel("DEBUG")
logger.addHandler(handler)
file_handler = FileHandler("nicobot.log")
file_handler.setFormatter(fmt)
file_handler.setLevel("DEBUG")
logger.addHandler(file_handler)

id_ = os.environ.get("ID")
pw = os.environ.get("PW")

player = NicoPlayer()
if id_ and pw:
    player.login(id_, pw)


class NicoAudioSource(FFMPEGAudioSource):
    def __init__(self, video, user, *args, **kwargs):
        super().__init__(None, *args, **kwargs)
        self.video = video
        self.user = user
        self.session = None

    def prepare(self):
        self.session = player.play(self.video.id)
        self.session.prepare("best", "worst")
        self.filename = self.session.start()
        super().prepare()

    def cleanup(self):
        self.session.stop_flag.set()
        super().cleanup()


class NicoBot:
    def __init__(self):
        self.color = 0xffbe97
        self.clients = {}
        self.players = {}
        self.channels = {}

    def embed(self, title, message, user):
        username = f"{user.username}#{user.discriminator}"

        embed = Embed(title=title, description=message, color=self.color)
        embed.set_footer(f"Requested by {username}", user.avatar)

        return embed

    def error_embed(self, message, user, title="An error has been occured!"):
        username = f"{user.username}#{user.discriminator}"
        
        embed = Embed(title=title, description=message, color=0xffff00)
        embed.set_footer(f"Requested by {username}", user.avatar)

        return embed

    def _callback(self, player):
        if len(player.queue) < 1:
            return
        song = player.queue[0]
        channel = player.client.get_channel()
        textchannel = self.channels.get(player.client.server_id)
        self.send_nowplaying(song, channel, textchannel)

    def send_nowplaying(self, song, channel, textchannel):
        songname = song.video.title
        songid = song.video.id
        songurl = f"https://www.nicovideo.jp/watch/{songid}"
        songthumb = song.video.thumbnail
        embed = self.embed(
            "Play",
            f"**`{channel.name}`: Now Playing [{songname}]({songurl}).**",
            song.user
        )
        embed.set_thumbnail(songthumb)
        textchannel.send(embed=embed)
        return embed

    def join(self, ctx):
        channel = ctx.guild.get_voice_state(ctx.user)

        if channel is None:
            return self.error_embed("You are not connected to VC. "
                                    "Please reconnect and try again.",
                                    ctx.user)

        vc = channel.connect()
        player = QueuedAudioPlayer(vc, callback=self._callback)

        self.clients.update({ctx.guild.id: vc})
        self.players.update({ctx.guild.id: player})
        self.channels.update({ctx.guild.id: None})

        return self.embed(
            "Join", f"Successfully joined {channel.name}!", ctx.user)

    def leave(self, ctx):
        player = self.players.get(ctx.guild.id)
        client = self.clients.get(ctx.guild.id)

        if player is None:
            return self.error_embed("I am not connected to VC!", ctx.user)
        if client.get_channel() != ctx.guild.get_voice_state(ctx.user):
            return self.error_embed("You are not in the VC!", ctx.user)

        player.stop()
        player.stop_flag.set()
        client.disconnect()
        self.clients.update({ctx.guild.id: None})
        self.players.update({ctx.guild.id: None})

        return self.embed("Leave", "Successfully left the channel!", ctx.user)


class NicobotEventHandler(ThreadedMethodEventHandler, InteractionEventHandler):
    def on_ready(self, obj):
        self.client.update_presence(
            activities=[{'type': 2, 'name': 'Orangestar'}])

    def on_resume(self, obj):
        self.on_ready(obj)


manager = SlashCommandManager()

nicobot = NicoBot()

join = SlashCommand(
    nicobot.join,
    "join",
    "Invite the bot to your current voice channel"
)

leave = SlashCommand(
    nicobot.leave,
    "leave",
    "Leave the current voice channel"
)

manager.register(join, leave)

client = DiscordInteractionClient(
    open("token").read().strip().rstrip().replace("\n", ""),
    handler=NicobotEventHandler,
    command_manager=manager
)

try:
    client.start()
    client.ready_to_run.wait()
    manager.update()
    client.join()
except KeyboardInterrupt:
    client.stop()
    client.join()
