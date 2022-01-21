from discordapi.slash import (
    SlashCommand, SubCommand, String, DiscordInteractionClient,
    InteractionEventHandler
)

from discordapi import QueuedAudioPlayer, FFMPEGAudioSource, Embed
from niconico import NicoPlayer

import os
import sys
import logging

from websocket import enableTrace
from logging import StreamHandler, FileHandler
from colorlog import ColoredFormatter


logger = logging.getLogger("nicobot")
logger.setLevel("DEBUG")
fmt = ColoredFormatter("%(log_color)s[%(levelname)s]|%(asctime)s|"
                       "%(threadName)s|%(funcName)s|: %(message)s")
handler = StreamHandler(sys.stdout)
handler.setFormatter(fmt)
handler.setLevel("INFO")
logger.addHandler(handler)
file_handler = FileHandler("nicobot.log")
file_handler.setFormatter(fmt)
file_handler.setLevel("DEBUG")
logger.addHandler(file_handler)

enableTrace(False, file_handler)

id_ = os.environ.get("ID")
pw = os.environ.get("PW")

player = NicoPlayer()
if id_ and pw:
    player.login(id_, pw)


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


class NicoBot:
    def __init__(self):
        self.color = 0xffbe97
        self.clients = {}
        self.players = {}

    def embed(self, title, message, user):
        username = f"{user.name}#{user.discriminator}"

        embed = Embed(title=title, description=message, color=self.color)
        embed.set_footer(f"Requested by {username}", user.avatar)

        return embed

    def error_embed(self, message, user, title="An error has been occured!"):
        username = f"{user.name}#{user.discriminator}"
        
        embed = Embed(title=title, description=message, color=0xffff00)
        embed.set_footer(f"Requested by {username}", user.avatar)

        return embed

    @SlashCommand.create(
        "Invite the bot to your current Voice Channel"
    )
    def join(self, ctx):
        channel = ctx.message.guild.voice_state.get(ctx.user.id)

        if channel is None:
            return self.error_embed("You are not connected to VC. "
                                    "Please reconnect and try again.",
                                    ctx.user)

        vc = channel.connect()
        player = QueuedAudioPlayer(vc, callback=self._callback)

        self.clients.update({ctx.guild.id: vc})
        self.players.update({ctx.guild.id: player})

        return self.embed(f"Successfully joined {channel.name}!")

    def leave(self, ctx):
        player = self.players.get(ctx.guild.id)
        client = self.clients.get(ctx.guild.id)

        if player is None:
            return self.error_embed("I am not connected to VC!", ctx.user)

        player.stop()
        player.stop_flag.set()
        client.disconnect()
        self.clients.update({ctx.guild.id: None})
        self.players.update({ctx.guild.id: None})

        return self.embed("Successfully left the channel!")
