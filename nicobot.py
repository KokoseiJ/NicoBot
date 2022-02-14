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

nicoplayer = NicoPlayer()
if id_ and pw:
    nicoplayer.login(id_, pw)


class NicoAudioSource(FFMPEGAudioSource):
    def __init__(self, video, user, *args, **kwargs):
        super().__init__(None, *args, **kwargs)
        self.video = video
        self.user = user
        self.session = None

    def prepare(self):
        self.session = nicoplayer.play(self.video.id)
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
        
        embed = Embed(title=title, description=message, color=0xff0000)
        embed.set_footer(f"Requested by {username}", user.avatar)

        return embed

    def _callback(self, player):
        if len(player.queue) < 1:
            return
        song = player.queue[0]
        voicechannel = player.client.get_channel()
        textchannel = self.channels.get(player.client.server_id)
        if textchannel is not None:
            self.send_nowplaying(song, voicechannel, textchannel)

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

        client = self.clients.get(ctx.guild.id)
        if client and channel == client.get_channel():
            return self.error_embed("I am already connected in this channel!",
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

    def play_nico(self, ctx, query):
        player = self.players.get(ctx.guild.id)
        client = self.clients.get(ctx.guild.id)

        if player is None:
            return self.error_embed("I am not connected to VC!", ctx.user)
        if client.get_channel() != ctx.guild.get_voice_state(ctx.user):
            return self.error_embed("You are not in the VC!", ctx.user)

        videos = None
        mylist = None
        type_, val = nicoplayer.parse_id(query)

        if type_ == 0:
            videos = nicoplayer.search(val, _limit=1)[:1]
            if not videos:
                return self.error_embed(
                    "Video was not found. Please try different keywords.",
                    ctx.user
                )
        elif type_ == 1:
            videos = [nicoplayer.get_thumb_info(val)]

        elif type_ == 2:
            mylist = nicoplayer.get_mylist(val)
            videos = mylist.items
        else:
            return "This should never happen. You win."

        sources = [NicoAudioSource(video, ctx.user) for video in videos]

        player.add_to_queue(sources)
        player.play()

        if type_ != 2:
            video = videos[0]
            url = f"https://www.nicovideo.jp/watch/{video.id}"
            desc = f"Added [{video.title}]({url}) to the queue!"
        else:
            url = f"https://www.nicovideo.jp/mylist/{val}"
            desc = f"Added mlist [{mylist.name}]({url}) to the queue!"

        embed = self.embed("Play", desc, ctx.user)
        embed.set_thumbnail(videos[0].thumbnail)

        return embed

    def stop(self, ctx):
        player = self.players.get(ctx.guild.id)
        client = self.clients.get(ctx.guild.id)

        if player is None:
            return self.error_embed("I am not connected to VC!", ctx.user)
        if client.get_channel() != ctx.guild.get_voice_state(ctx.user):
            return self.error_embed("You are not in the VC!", ctx.user)

        player.queue.clear()
        player.stop()

        return self.embed("Stop", "Stopped Playing.", ctx.user)

    def skip(self, ctx):
        player = self.players.get(ctx.guild.id)
        client = self.clients.get(ctx.guild.id)

        if player is None:
            return self.error_embed("I am not connected to VC!", ctx.user)
        if client.get_channel() != ctx.guild.get_voice_state(ctx.user):
            return self.error_embed("You are not in the VC!", ctx.user)

        player.stop()

        return self.embed("Skip", "Skipped the music.", ctx.user)

    def pause(self, ctx):
        player = self.players.get(ctx.guild.id)
        client = self.clients.get(ctx.guild.id)

        if player is None:
            return self.error_embed("I am not connected to VC!", ctx.user)
        if client.get_channel() != ctx.guild.get_voice_state(ctx.user):
            return self.error_embed("You are not in the VC!", ctx.user)

        if player.is_paused():
            return self.embed("Pause", "Player has already been paused!",
                              ctx.user)
        else:
            player.pause()
            return self.embed("Pause", "Paused the music.", ctx.user)

    def resume(self, ctx):
        player = self.players.get(ctx.guild.id)
        client = self.clients.get(ctx.guild.id)

        if player is None:
            return self.error_embed("I am not connected to VC!", ctx.user)
        if client.get_channel() != ctx.guild.get_voice_state(ctx.user):
            return self.error_embed("You are not in the VC!", ctx.user)

        if not player.is_paused():
            return self.embed("Resume", "Player is already playing!", ctx.user)
        else:
            player.resume()
            return self.embed("Resume", "Resumed the music.", ctx.user)

    def notify(self, ctx):
        player = self.players.get(ctx.guild.id)
        client = self.clients.get(ctx.guild.id)

        if player is None:
            return self.error_embed("I am not connected to VC!", ctx.user)
        if client.get_channel() != ctx.guild.get_voice_state(ctx.user):
            return self.error_embed("You are not in the VC!", ctx.user)

        channel = self.channels.get(ctx.guild.id)
        if channel is None:
            self.channels.update({ctx.guild.id: ctx.channel})
            return self.embed("Notify", "Set the notification channel to "
                                        f"{ctx.channel.name}!", ctx.user)
        else:
            self.channels.update({ctx.guild.id: None})
            return self.embed("Notify", "Disabled notification!", ctx.user)


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

play_nico = SlashCommand(
    nicobot.play_nico,
    "nico",
    "Search/Play music from nicovideo.",
    (
        String("query", "Search query/id/url", required=True),
    )
)

stop = SlashCommand(
    nicobot.stop,
    "stop",
    "Stops the music."
)

skip = SlashCommand(
    nicobot.skip,
    "skip",
    "Skips the music."
)

pause = SlashCommand(
    nicobot.pause,
    "pause",
    "Pauses the music."
)

resume = SlashCommand(
    nicobot.resume,
    "resume",
    "Resumes the music."
)

notify = SlashCommand(
    nicobot.notify,
    "notify",
    "Toggles the notification when the song plays."
)

play = SubCommand(
    "play",
    play_nico
)

manager.register(join, leave, play, stop, skip, pause, resume, notify)

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
