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

from .guild import Guild
from .user import BotUser
from .member import Member
from .message import Message
from .channel import get_channel
from .websocket import WebSocketThread
from .const import LIB_NAME, GATEWAY_URL
from .handler import EventHandler, GeneratorEventHandler

import sys
import time
import logging
from threading import Event
from websocket import STATUS_ABNORMAL_CLOSED

__all__ = []

logger = logging.getLogger(LIB_NAME)


class DiscordGateway(WebSocketThread):
    """Gateway Class which defines websocket behaviour and handles events.

    Event related operations are done within this class.
    """
    DISPATCH = 0
    HEARTBEAT = 1
    IDENTIFY = 2
    PRESENCE_UPDATE = 3
    VOICE_STATE_UPDATE = 4
    RESUME = 6
    RECONNECT = 7
    REQUEST_GUILD_MEMBERS = 8
    INVALID_SESSION = 9
    HELLO = 10
    HEARTBEAT_ACK = 11

    def __init__(self, token, handler=None, event_parser=None, intents=32509,
                 name="main"):
        # 32509 is an intent value that omits flags which require verification
        super(DiscordGateway, self).__init__(
            GATEWAY_URL,
            self._dispatcher,
            name
        )

        if handler is None:
            handler = GeneratorEventHandler
        if event_parser is None:
            event_parser = GatewayEventParser

        self.set_handler(handler)
        self.event_parser = event_parser(self)

        self.token = token
        self.intents = intents

        self.seq = 0
        self.heartbeat_interval = None
        self.is_heartbeat_ready = Event()
        self.heartbeat_ack_received = Event()
        self.is_reconnect = False
        self.voice_queue = {}
        self.voice_clients = {}

        self.user = None
        self.guilds = None
        self.session_id = None
        self.application = None

    def set_ready(
            self, user=None, guilds=None, session_id=None, application=None):
        if None not in [user, guilds, session_id, application]:
            self.user = BotUser(self, user)
            self.guilds = {obj['id']: False for obj in guilds}
            self.session_id = session_id
            self.application = application
        self.ready_to_run.set()

    def add_voice_queue(self, guild_id, event, payload):
        # Puts data into voice_queue so that GuildVoiceChannel.connect
        # method can start a voice session
        if self.voice_queue.get(guild_id) is None:
            return

        self.voice_queue[guild_id].put((event, payload))

    def set_handler(self, handler):
        if isinstance(handler, EventHandler):
            self.handler = handler
        elif issubclass(handler, EventHandler):
            self.handler = handler()
        else:
            raise TypeError("Inappropriate EventHandler object.")

        self.handler.set_client(self)

    def init_connection(self):
        self.is_heartbeat_ready.wait()
        if not self.is_reconnect:
            self.send_identify()
            self.is_reconnect = True
        else:
            self.send_resume()

    def send_identify(self):
        try:
            # Reuse_activities if it was already set
            activities = self._activities
            if not self._activities:
                activities = None
        except NameError:
            activities = None

        data = self._get_payload(
            self.IDENTIFY,
            token=self.token,
            intents=self.intents,
            properties={
                "$os": sys.platform,
                "$browser": LIB_NAME,
                "$device": LIB_NAME
            },
        )

        if activities:
            data.update({
                "presence": {
                    "since": time.time() * 1000,
                    "activities": activities,
                    "afk": False,
                    "status": None
                }
            })

        self.send(data)

    def send_resume(self):
        data = self._get_payload(
            self.RESUME,
            token=self.token,
            session_id=self.session_id,
            seq=self.seq
        )
        self.send(data)

    def do_heartbeat(self):
        self.is_heartbeat_ready.wait()

        stop_flag = self.heartbeat_thread.stop_flag
        wait_time = self.heartbeat_interval

        while not stop_flag.is_set() and self.is_heartbeat_ready.wait():
            logger.debug("Sending heartbeat...")
            sendtime = time.time()
            self.send_heartbeat()

            deadline = sendtime + wait_time

            if stop_flag.wait(deadline - time.time()):
                break

            if not self.heartbeat_ack_received.is_set():
                logger.error("No HEARTBEAT_ACK received within time!")
                self._sock.close(STATUS_ABNORMAL_CLOSED)

            self.heartbeat_ack_received.clear()

        logger.debug("Terminating heartbeat thread...")

    def send_heartbeat(self):
        data = self._get_payload(
            self.HEARTBEAT,
            d=self.seq if self.seq else None
        )
        self.send(data)

    def _get_payload(self, op, d=None, **data):
        return {
            "op": op,
            "d": data if d is None else d
        }

    def cleanup(self):
        self.is_heartbeat_ready.clear()

        for client in self.voice_clients.values():
            client.stop()

    def _dispatcher(self, data):
        op = data['op']
        payload = data['d']
        seq = data['s']
        event = data['t']

        if op == self.DISPATCH:
            self.seq = seq
            obj = self.event_parser._handle(event, payload)
            self.handler.handle(event, obj)

        elif op == self.INVALID_SESSION or op == self.RECONNECT:
            self.is_reconnect = payload
            self._sock.close()

        elif op == self.HELLO:
            self.heartbeat_interval = payload['heartbeat_interval'] / 1000
            self.is_heartbeat_ready.set()

        elif op == self.HEARTBEAT_ACK:
            logger.debug("Received Heartbeat ACK!")
            self.heartbeat_ack_received.set()

    def __str__(self):
        class_name = self.__class__.__name__
        if self.user is not None:
            username = self.user.username
            tag = self.user.discriminator
            username_full = f"{username}#{tag}"
            id_ = self.user.id
        else:
            username_full = None
            id_ = None
        return f"<{class_name} '{username_full}' ({id_})>"

    def __repr__(self):
        return self.__str__()


class GatewayEventParser:
    def __init__(self, client=None):
        self.client = None
        if client:
            self._set_client(client)

    def _set_client(self, client):
        if not isinstance(client, DiscordGateway):
            raise TypeError("client should be DiscordGateway, "
                            f"not '{type(client)}'")
        self.client = client

    def _handle(self, event, payload):
        name = "on_" + event.lower()
        handler = getattr(self, name, None)
        if handler is None:
            logger.debug(f"Unimplemented Event {event}")
            return payload

        value = handler(payload)

        if value is None:
            value = payload

        return value

    def on_ready(self, payload):
        self.client.set_ready(
            payload['user'],
            payload['guilds'],
            payload['session_id'],
            payload['application']
        )

    def on_resumed(self, payload):
        self.client.set_ready()

    def on_channel_create(self, payload):
        obj = get_channel(self.client, payload)
        
        guild_id = obj.guild_id
        if guild_id is None:
            return obj

        guild = self.client.guilds.get(guild_id)
        id_ = obj.id

        guild.channels.update({id_: obj})

        return obj

    def on_channel_update(self, payload):
        return self.on_channel_create(payload)

    def on_channel_delete(self, payload):
        obj = get_channel(self.client, payload)
        
        guild_id = obj.guild_id
        if guild_id is None:
            return obj

        guild = self.client.guilds.get(guild_id)
        id_ = obj.id

        if guild.channels.get(id_) is not None:
            del guild.channels[id_]

        return obj

    def on_channel_pins_update(self, payload):
        guild_id = payload.get("guild_id")
        if guild_id is not None:
            channel_id = payload.get("channel_id")
            timestamp = payload.get("last_pin_timestamp")
            guild = self.client.guilds.get(guild_id)
            if guild:
                channel = guild.channels.get(channel_id)
            channel.last_pin_timestamp = timestamp

    def on_guild_create(self, payload):
        obj = Guild(self.client, payload)
        self.client.guilds[obj.id] = obj
        return obj

    def on_guild_update(self, payload):
        return self.on_guild_create(payload)

    def on_guild_delete(self, payload):
        self.client.guilds[payload.get("id")] = False

    def on_guild_ban_add(self, payload):
        guild = self.client.guilds.get(payload.get('guild_id'))
        if not guild:
            return

        user_id = payload.get("user").get("id")
        member = guild.members.get(user_id)
        if member is not None:
            del guild.members[user_id]

    def on_guild_emojis_update(self, payload):
        guild = self.client.guilds.get(payload.get('guild_id'))
        if not guild:
            return

        guild.emojis = payload.get('emojis')

    def on_guild_member_add(self, payload):
        guild = self.client.guilds.get(payload('guild_id'))
        if not guild:
            return

        del payload['guild_id']
        obj = Member(self.client, guild, payload)

        guild.members.append(obj)

        return obj

    def on_guild_member_remove(self, payload):
        guild = self.client.guilds.get(payload('guild_id'))
        if not guild:
            return

        del guild.members[payload.get("user").get("id")]

    def on_guild_member_update(self, payload):
        guild = self.client.guilds.get(payload('guild_id'))
        if not guild:
            return

        user_id = payload.get("user").get("id")
        del payload['guild_id']
        member = guild.members.get(user_id)
        member.__init__(self.client, guild, payload)

    def on_guild_members_chunk(self, payload):
        guild = self.client.guilds.get(payload('guild_id'))
        if not guild:
            return

        memberobjs = payload.get("members")
        members = {
            member['user']['id']: Member(self.client, guild, member)
            for member in memberobjs
        }
        guild.members.update(members)

    def on_message_create(self, payload):
        if payload.get("author") is None:
            return
        return Message(self.client, payload)

    def on_message_update(self, payload):
        return self.on_message_create(payload)

    def on_voice_server_update(self, payload, event="VOICE_SERVER_UPDATE"):
        guild_id = payload.get("guild_id")
        self.client.add_voice_queue(guild_id, event, payload)

    def on_voice_state_update(self, payload):
        if payload['user_id'] == self.client.user.id:
            self.on_voice_server_update(payload, "VOICE_STATE_UPDATE")

    def on_presence_update(self, payload):
        # Silencing frequent warning
        pass

    # Add GUILD_ROLE event
