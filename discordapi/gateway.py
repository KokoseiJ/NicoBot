#
# NicoBot is Nicovideo Player bot for Discord, written from the scratch.
# This file is part of NicoBot.
#
# Copyright (C) 2020 Wonjun Jung (KokoseiJ)
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
from .util import SelectableEvent
from .websocket import WebSocketThread
from .const import LIB_NAME, GATEWAY_URL

import sys
import time
import logging
from select import select
from websocket import STATUS_ABNORMAL_CLOSED

logger = logging.getLogger(LIB_NAME)

__all__ = []


class DiscordGateway(WebSocketThread):
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

    def __init__(self, token, handler, intents=32509, name="main"):
        # 32509 is an intent value that omits flags that require verification
        super(DiscordGateway, self).__init__(
            GATEWAY_URL,
            self._dispatcher,
            name
        )
        self.token = token
        self.event_handler = handler
        self.intents = intents

        self.seq = 0
        self.heartbeat_interval = None
        self.is_heartbeat_ready = SelectableEvent()
        self.heartbeat_ack = SelectableEvent()
        self.is_reconnect = False
        self.voice_queue = {}
        self.voice_clients = []

        self.user = None
        self.guilds = None
        self.session_id = None
        self.application = None

    def init_connection(self):
        self.is_heartbeat_ready.wait()
        if not self.is_reconnect:
            self.send_identify()
            self.is_reconnect = True
        else:
            self.send_resume()

    def send_identify(self):
        data = self._get_payload(
            self.IDENTIFY,
            token=self.token,
            intents=self.intents,
            properties={
                "$os": sys.platform,
                "$browser": LIB_NAME,
                "$device": LIB_NAME
            }
        )
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
        select((self.is_heartbeat_ready, stop_flag), (), ())

        while not stop_flag.is_set() and self.is_heartbeat_ready.wait():
            logger.debug("Sending heartbeat...")
            sendtime = time.time()
            self.send_heartbeat()

            deadline = sendtime + wait_time
            selectlist = (stop_flag, self.heartbeat_ack)
            rl, _, _ = select(selectlist, (), (), deadline - time.time())

            if stop_flag in rl:
                break
            elif self.heartbeat_ack not in rl:
                logger.error("No HEARTBEAT_ACK received within time!")
                self.sock.close(STATUS_ABNORMAL_CLOSED)

            self.heartbeat_ack.clear()

            rl, _, _ = select((stop_flag,), (), (), deadline - time.time())
            if stop_flag in rl:
                break

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

        for client in self.voice_clients:
            client.stop()

    def _dispatcher(self, data):
        op = data['op']
        payload = data['d']
        seq = data['s']
        event = data['t']

        if op == self.DISPATCH:
            self.seq = seq
            self._event_parser(event, payload)

        elif op == self.INVALID_SESSION or op == self.RECONNECT:
            self.is_reconnect = payload
            self.sock.close()

        elif op == self.HELLO:
            self.heartbeat_interval = payload['heartbeat_interval'] / 1000
            self.is_heartbeat_ready.set()

        elif op == self.HEARTBEAT_ACK:
            logger.debug("Received Heartbeat ACK!")
            self.heartbeat_ack.set()

    def _event_parser(self, event, payload):

        obj = payload

        if event == "READY":
            self.user = BotUser(self, payload['user'])
            self.guilds = {obj['id']: False for obj in payload['guilds']}
            self.session_id = payload['session_id']
            self.application = payload['application']
            self.ready_to_run.set()

        elif event == "RESUMED":
            self.ready_to_run.set()

        elif event.startswith("CHANNEL") and event != "CHANNEL_PINS_UPDATE":
            obj = get_channel(self, payload)

            guild_id = obj.guild_id
            if guild_id is not None:
                guild = self.guilds.get(guild_id)
                id = obj.id
                event_sub = event.split("_", 1)[-1]
                if event_sub == "CREATE" or event_sub == "UPDATE":
                    guild.channels.update({
                        id: obj
                    })
                elif event_sub == "DELETE":
                    if guild.channels.get(id) is not None:
                        del guild.channel[id]

        elif event == "CHANNEL_PINS_UPDATE":
            guild_id = payload.get("guild_id")
            if guild_id is not None:
                channel_id = payload.get("channel_id")
                timestamp = payload.get("last_pin_timestamp")
                guild = self.guilds.get(guild_id)
                channel = guild.channels.get(channel_id)
                channel.last_pin_timestamp = timestamp

        elif event == "GUILD_CREATE" or event == "GUILD_UPDATE":
            obj = Guild(self, payload)
            id = obj.id
            self.guilds[id] = obj
        
        elif event == "GUILD_DELETE":
            self.guilds[id] = False

        elif event == "GUILD_BAN_ADD":
            guild_id = payload.get("guild_id")
            user_id = payload.get("user").get("id")
            guild = self.guilds.get(guild_id)
            member = guild.members.get(user_id)
            if member is not None:
                del guild.members[user_id]

        elif event == "GUILD_EMOJIS_UPDATE":
            guild_id = payload.get("guild_id")
            guild = self.guilds.get(guild_id)
            guild.emojis = payload.get("emojis")

        elif event == "GUILD_MEMBER_ADD":
            guild_id = payload.get("guild_id")
            guild = self.guilds.get(guild_id)
            del payload['guild_id']
            obj = Member(self, guild, payload)
            guild = self.guilds.get(guild_id)
            guild.members.append(obj)

        elif event == "GUILD_MEMBER_REMOVE":
            guild_id = payload.get("guild_id")
            user_id = payload.get("user").get("id")
            guild = self.guilds.get(guild_id)
            del guild.members[user_id]

        elif event == "GUILD_MEMBER_UPDATE":
            guild_id = payload.get("guild_id")
            user_id = payload.get("user").get("id")
            del payload['guild_id']
            guild = self.guilds.get(guild_id)
            member = guild.members.get(user_id)
            member.__init__(self, guild, payload)

        elif event == "GUILD_MEMBERS_CHUNK":
            guild_id = payload.get("guild_id")
            guild = self.guilds.get(guild_id)
            memberobjs = payload.get("members")
            members = {
                member['user']['id']: Member(self, guild, member)
                for member in memberobjs
            }
            guild = self.guilds.get(guild_id)
            guild.members.update(members)

        elif event == "MESSAGE_CREATE" or event == "MESSAGE_UPDATE":
            obj = Message(self, payload)

        elif (event == "VOICE_STATE_UPDATE" and
                payload['user_id'] == self.user.id) or\
                event == "VOICE_SERVER_UPDATE":
            if self.voice_queue.get(payload['guild_id']) is not None:
                self.voice_queue[payload['guild_id']].put((event, payload))

        # Add GUILD_ROLE event

        self.event_handler(event, obj)
