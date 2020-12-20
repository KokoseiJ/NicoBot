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

from .user import User
from .channel import Channel
from .guild import Guild, Member
from .event_handler import GeneratorEventHandler
from .const import GATEWAY_URL, GATEWAY_VERSION, INTENTS_DEFAULT,\
                             NAME

import sys
import json
import time
import logging
from sys import platform
from traceback import print_exc
from websocket import WebSocketApp
from threading import Thread, Event

URL = GATEWAY_URL.format(GATEWAY_VERSION)

logger = logging.getLogger(NAME)


def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    logger.error(
        "Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))


sys.excepthook = handle_exception


class DiscordGateway:
    def __init__(self, token, intents=None, event_handler=None):
        """
        This class defines the connection to discord gateway.

        This class will internally run 2 threads-
        gateway_heartbeat, gateway_run.
        It also runs gateway_init at the beginning, which gets terminated after
        identifying with discord gateway has been completed.

        Attributes:
            token:
                represents discord token which will be used when authorizing
                the client and issuing the voice connection.
            intents:
                Intents that will be sent when identifying.
                WARNING! Default value is 32509, which doesn't include
                `GUILD_MEMBERS`, `GUILD_PRESENCES`. If you wish to use these,
                You have to first enable them in your bot dashboard, and
                initialize gateway with this parameter set to 32767.
            event_handler:
                Handler that will be used to handle events sent by gateway.
            heartbeat_interval:
                Heartbeat interval sent in `hello`(Opcode 10), *in msec.*
            sequence:
                sequence received from discord gateway.
            ready_data:
                data received from discord gateway when `READY` event has
                been issued.
            user:
                User object present in ready_data.
            guilds:
                Guilds present in ready_data.
            session_id:
                Session ID present in ready_data.
            application:
                application object present in ready_data.
            run_thread:
                thread where websocket connection is running. This thread will
                also attempt to reconnect to gateway when it disconnects.
            heartbeat_thread:
                thread where heartbeat is happening.
            is_connected:
                Event object representing if gateway has been responded with
                `hello`(Opcode 10). When client disconnects, this gets cleared.
                If you want to check if gateway is prepared to use, You should
                use is_ready instead.
            is_ready:
                Event object representing if identification between gateway and
                client has been completed, and is now in connected state.
                You can use this event to ensure if client is connected to
                gateway.
            got_respond:
                Event object used to determine if server has returned Resume or
                Invalid Session when resuming connection.
            heartbeat_ack_received:
                Event used to check if heartbeat ACK has been received by
                client. since heartbeat thread can't directly receive websocket
                messages, This event should be used.
            restart_heartbeat:
                Flag to indicate if heartbeat should be restarted.
            is_restart_required:
                Event used to determine if connection is resumable or it should
                be reconnected when disconnection happens.
            is_stop_requested:
                Event used to determine if cilent needs to attempt to reconnect
                to gateway or just stop the connection completely.
            websocket:
                WebSocketApp object used for communication. Using this
                attribute directly to communicate with gateway is not
                recommended, please inherit this class and override
                methods with your own needs.
        """
        self.token = token
        self.intents = intents if intents is not None else INTENTS_DEFAULT
        self.event_handler = event_handler(self) if event_handler is not None\
            else GeneratorEventHandler(self)

        self.heartbeat_interval = None
        self.sequence = None

        self.ready_data = None
        self.user = None
        self.guilds = None
        self.session_id = None
        self.application = None

        self.run_thread = None
        self.heartbeat_thread = None

        self.is_connected = Event()
        self.is_ready = Event()
        self.got_respond = Event()
        self.heartbeat_ack_received = Event()
        self.restart_heartbeat = Event()
        self.is_restart_required = Event()
        self.is_stop_requested = Event()

        self.websocket = None

    def connect(self):
        """
        Runs heartbeat_thread, run_thread and hangs until is_ready is set.
        """
        if self.run_thread and self.run_thread.is_alive():
            raise RuntimeError("Thread is already running!")

        logger.info("Starting heartbeat thread.")
        self.heartbeat_thread = Thread(
            target=self._heartbeat,
            name="gateway_heartbeat"
        )
        self.heartbeat_thread.start()

        logger.info("Starting run thread.")
        self.run_thread = Thread(
            target=self._connect,
            name="gateway_run"
        )
        self.run_thread.start()

        logger.info("Waiting for client to get ready...")
        self.is_ready.wait()
        logger.info("Connection established!")

    def disconnect(self):
        """
        Sets is_stop_requested, and kills the websocket.
        """
        logger.info("Setting is_stop_requested and killing websocket...")
        self.is_stop_requested.set()
        self.websocket.close()

    def _connect(self):
        """
        Creates websocket, run it, attempts to reconnect when it disconencts.
        """
        logger.info("Creating websocket...")
        self.websocket = WebSocketApp(
            URL,
            on_message=lambda ws, msg:  self._on_message(ws, msg),
            on_error=lambda ws, error: logger.error(error),
            on_open=lambda ws:  Thread(
                target=self._gateway_init,
                args=(ws,),
                name="gateway_init"
            ).start()
        )
        while True:
            logger.info("Connecting to websocket...")
            self.websocket.run_forever()

            logger.warning("Websocket disconnected!")
            if not self.is_connected.is_set():
                logger.error("Server unreachable, stopping this thread...")
                return
            self.is_connected.clear()
            self.is_ready.clear()
            self.got_respond.clear()
            self.heartbeat_ack_received.clear()
            self.restart_heartbeat.set()
            if self.is_stop_requested.is_set():
                logger.info("is_stop_requested set, stopping this thread...")
                return
            elif self.is_restart_required.is_set() or self.session_id is None:
                logger.info("Restart required, creating new websocket "
                            "with _gateway_init...")
                self.is_restart_required.clear()
                self.sequence = None
                self.websocket = WebSocketApp(
                    URL,
                    on_message=lambda ws, msg:  self._on_message(ws, msg),
                    on_open=lambda ws:  Thread(
                        target=self._gateway_init,
                        args=(ws,),
                        name="gateway_init"
                    ).start()
                )
            else:
                logger.info("Creating new websocket with _gateway_resume...")
                self.websocket = WebSocketApp(
                    URL,
                    on_message=lambda ws, msg:  self._on_message(ws, msg),
                    on_open=lambda ws:  Thread(
                        target=self._gateway_resume,
                        args=(ws,),
                        name="gateway_init"
                    ).start()
                )
            self.is_stop_requested.clear()
            self.is_restart_required.clear()

    def _gateway_init(self, ws):
        """
        Initialize gateway.
        """
        logger.info("Waiting for gateway to send Hello...")
        self.is_connected.wait()
        logger.info("Sending Identify payload...")
        payload = {
            "op": 2,
            "d": {
                "token": self.token,
                "intents": self.intents,
                "properties": {
                    "$os": platform,
                    "$browser": NAME,
                    "$device": NAME
                }
            }
        }
        ws.send(json.dumps(payload))
        logger.info("Waiting for reply...")
        self.got_respond.wait()

    def _gateway_resume(self, ws):
        """
        Resumes gateway connection when it disconnects.
        """
        logger.info("Waiting for gateway to send Hello...")
        self.is_connected.wait()
        logger.info("Sending Resume payload...")
        payload = {
            "op": 6,
            "d": {
                "token": self.token,
                "session_id": self.ready_data['session_id'],
                "seq": self.sequence
            }
        }
        ws.send(json.dumps(payload))
        logger.info("Waiting for reply...")

        self.got_respond.wait()

    def _heartbeat(self):
        """
        It does the heartbeat. kinda self-explanatory.
        Since heartbeating really doesn't require recreating the whole thread
        between resuming, This thread remains through disconnects.
        It uses `websocket` attribute, so its sending target also gets changed
        whenever client establishes new connection.
        Since it waits until `is_connected` is set, It shouldn't send message
        to unconnected websocket.
        It checks if ACK has been received with `heartbeat_ack_received` event,
        which gets set by `_on_message`.
        """
        logger.info("Heartbeat started! waiting for client to get ready...")
        while True:
            self.is_connected.wait()
            logger.info("Sending heartbeat...")
            payload = {
                "op": 1,
                "d": self.sequence
            }
            self.websocket.send(json.dumps(payload))
            if self.restart_heartbeat.wait(int(self.heartbeat_interval/1000)):
                self.restart_heartbeat.clear()
                if self.is_stop_requested.is_set():
                    logger.info("is_stop_requested set. stopping heartbeat...")
                    return
                logger.info(
                    "Heartbeat restart requested, skipping this ACK...")
                continue
            if not self.is_connected.is_set() and\
                    self.heartbeat_ack_received.is_set():
                logger.error("Server didn't return ACK! closing websocket...")
                self.websocket.close(status=1006)
            self.heartbeat_ack_received.clear()

    def _on_message(self, ws, msg):
        """
        Handles messages sent by discord server.
        """
        payload = json.loads(msg)
        op = payload['op']
        data = payload['d']
        logger.debug(payload)

        if op == 10:
            self.heartbeat_interval = data['heartbeat_interval']
            self.is_connected.set()
        elif op == 9:
            if not data:
                self.is_restart_required.set()
            self.got_respond.set()
            self.websocket.close()
        elif op == 11:
            logger.info("Received Heartbeat ACK!")
            self.heartbeat_ack_received.set()
        elif op == 0:
            if self.sequence is not None and self.sequence+1 != payload['s']:
                self.websocket.close()
            self.sequence = payload['s']
            event = payload['t']

            if event == "READY":
                self.ready_data = data
                self.user = User(data['user'], self)
                self.guilds = {
                    guild['id']: False for guild in data['guilds']}
                self.session_id = data['session_id']
                self.got_respond.set()
                self.is_ready.set()

            elif event == "RESUMED":
                self.got_respond.set()
                self.is_ready.set()

            elif event == "CHANNEL_CREATE":
                channel = Channel(data, self)
                channel.guild.channels[channel.id] = channel

            elif event == "CHANNEL_UPDATE":
                if data.get("guild_id") is not None:
                    guild = self.guilds.get(data['guild_id'])
                    channel = guild.channels.get(data['id'])
                    for key, val in zip(data.keys(), data.values()):
                        setattr(channel, key, val)

            elif event == "CHANNEL_DELETE":
                guild = self.guilds.get(data['guild_id'])
                del guild.channels[data['id']]

            elif event == "CHANNEL_PINS_UPDATE":
                if data.get("guild_id") is not None:
                    guild = self.guilds[data['guild_id']]
                    channel = guild.channels[data['channel_id']]
                    channel.last_pin_timestamp = data['last_pin_timestamp']

            elif event == "GUILD_CREATE":
                try:
                    guild = Guild(data, self)
                    self.guilds[guild.id] = guild
                except Exception:
                    print_exc()

            elif event == "GUILD_UPDATE":
                guild = self.guilds.get(data['id'])
                for key, val in zip(data.keys(), data.values()):
                    setattr(guild, key, val)

            elif event == "GUILD_DELETE":
                if data.get('unavailable'):
                    self.guilds[data['id']] = False
                else:
                    del self.guilds[data['ID']]

            elif event == "GUILD_MEMBER_ADD":
                member = Member(data, self)
                guild = self.guilds.get(member.guild_id)
                guild.members[member.user.id] = member

            elif event == "GUILD_MEMBER_REMOVE":
                guild = self.guilds.get(data['guild_id'])
                del guild.members[data['user']['id']]

            elif event == "GUILD_MEMBER_UPDATE":
                data['user'] = User(data['user'], self)
                guild = self.guilds.get(data['guild_id'])
                member = guild.members.get(data['user'].id)
                for key, val in zip(data.keys(), data.values()):
                    setattr(member, key, val)

            self.event_handler.handler(event, data, msg)
