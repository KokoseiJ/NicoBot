# NicoBot - Nicovideo player bot for discord, written from the scratch
# Copyright (C) 2020 Wonjun Jung (Kokosei J)
#
#    This program is free software: you can redistribute it and/or modify
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

from discordapi import USER_AGENT, API_URL, event

from discordapi.user import User
from discordapi.gateway import Gateway
from discordapi.message import Message
from discordapi.util import get_channel
from discordapi.voice import VoiceClient
from discordapi.guild import PartialGuild, Guild

import json
import queue
import urllib.request
from urllib.parse import urljoin


class DiscordClient:
    def __init__(self, token):
        # TODO: Add Gateway connecting method and init it at here.
        #       also Voice Client should be separated
        # TODO: get user informations at init time and use it in repr value
        # TODO: User object should be added first lol
        self.token = token
        self.header = {
            "User-Agent": USER_AGENT,
            "Authorization": f"Bot {token}"
        }
        self.gateway = Gateway(token, self.event_handler)
        self.debug = False

    def event_generator(self):
        while not self.gateway.is_close_requested.is_set():
            try:
                yield self.gateway.event_queue.get(timeout=0.1)
            except queue.Empty:
                pass
        yield None, None

    def event_handler(self, typ, dat):
        if self.debug:
            print(dat)

        if typ in [
            event.CHANNEL_CREATE,
            event.CHANNEL_UPDATE,
            event.CHANNEL_DELETE
        ]:
            return get_channel(dat)
        elif typ in [event.GUILD_CREATE, event.GUILD_UPDATE]:
            return Guild(dat, self)
        elif typ in [event.MESSAGE_CREATE, event.MESSAGE_UPDATE]:
            if not dat.get("content") is None:
                return Message(dat, self)
        return typ, dat

    def voice_connect(self, channel, mute=False, deaf=False):
        user_id = self.get_my_user().id
        guild_id = channel.guild.id
        channel_id = channel.id
        session_id, token, guild_id, endpoint = self.gateway.voice_connect(
            guild_id, channel_id, mute, deaf)

        voice_client = VoiceClient(
            endpoint, guild_id, user_id, session_id, token)

        return voice_client

    def get_partial_guilds(self):
        endpoint = urljoin(API_URL, "users/@me/guilds")
        req = urllib.request.Request(endpoint, headers=self.header)
        with urllib.request.urlopen(req) as res:
            if res.status != 200:
                raise ValueError(f"Server returned code {res.status}.\n"
                                 f"Body: {res.read().encode()}")
            obj_list = json.loads(res.read())
            return [PartialGuild(obj, self) for obj in obj_list]

    def get_guilds(self):
        return [Guild(obj, self) for obj in self.gateway.guild_list]

    def get_guild(self, id):
        guild = [g for g in self.get_guilds() if g.id == id]
        return guild[0] if guild else None

    def get_my_user(self):
        return User(self.gateway.ready_data['user'])

    def get_user(self, id):
        endpoint = urljoin(API_URL, f"users/{id}")
        req = urllib.request.Request(endpoint, headers=self.header)
        with urllib.request.urlopen(req) as res:
            if res.status != 200:
                raise ValueError(f"Server returned code {res.status}.\n"
                                 f"Body: {res.read().encode()}")
            obj = json.loads(res.read())
            return User(obj)
