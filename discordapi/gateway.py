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

from .const import INTENTS_DEFAULT, GATEWAY_URL, LIB_NAME
from .websocket import WebSocketClient, SelectableEvent

import json
import time
import logging

from sys import platform
from select import select
from websocket import STATUS_ABNORMAL_CLOSED


logger = logging.getLogger(LIB_NAME)


class DiscordGateway(WebSocketClient):
    """
    Client used to connect to Discord main gateway.

    Attributes:
        handler: Event handler object used to handle event dispatch.
        token: Discord token to be used when connecting.
        intents: Intents value to be sent. default value is 32509.
        heartbeat_interval: Heartbeat interval received from the server.
        sequence: sequence number received from the server.
        user: User object representing the bot.
        guilds: List of guild objects the bot is in.
        session_id: ID of this session
        application: Application object representing the bot.
        heartbeat_ready: Event that indicates if heartbeat_interval has been
                         received.
        heartbeat_ack: Event that indicates if the heartbeat ACK has been
                       receieved.
        is_ready: Indicates if Ready data has bee acquired.
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

    def __init__(self, token, handler, intents=INTENTS_DEFAULT):
        super().__init__(GATEWAY_URL)
        self.handler = None
        self.token = token
        self.intents = intents

        self.heartbeat_interval = None
        self.sequence = 0

        self.user = None
        self.guilds = None
        self.session_id = None
        self.application = None

        self.heartbeat_ready = SelectableEvent()
        self.heartbeat_ack = SelectableEvent()
        self.is_ready = SelectableEvent()

        if handler is not None:
            self.set_handler(handler)

    def clean(self):
        super().clean()
        self.is_ready.clear()
        self.heartbeat_ready.clear()
        self.heartbeat_ack.clear()
        self.heartbeat_interval = None

    def connect_threaded(self):
        super().connect_threaded()
        self.is_ready.wait()
        return self.connection_thread

    def on_connect(self, ws):
        self.sequence = 0
        self.heartbeat_ready.wait()
        self.run_heartbeat()
        logger.debug("Sending IDENTIFY event...")
        ws.send(json.dumps({
            "op": self.IDENTIFY,
            "d": {
                "token": self.token,
                "intents": self.intents,
                "properties": {
                    "$os": platform,
                    "$browser": LIB_NAME,
                    "$device": LIB_NAME
                }
            }
        }))

    def on_reconnect(self, ws):
        if not self.session_id:
            logging.debug("Connection was not RESUMEable, reconnecting...")
            return self.on_connect(ws)
        self.heartbeat_ready.wait()
        self.run_heartbeat()
        logger.debug("Sending RESUME event with session id "
                     f"{self.session_id}...")
        ws.send(json.dumps({
            "op": self.RESUME,
            "d": {
                "token": self.token,
                "session_id": self.session_id,
                "seq": self.sequence
            }
        }))

    def on_message(self, data):
        logger.debug(f"Client received data {data}")
        if data['s'] is not None:
            self.sequence = data['s']
        op = data['op']
        _type = data['t']
        data = data['d']

        if op == self.DISPATCH:
            if _type == "READY":
                # self.ready_data = data
                self.user = data['user']
                self.guilds = data['guilds']
                self.session_id = data['session_id']
                self.application = data['application']

                self.is_ready.set()
            elif _type == "RESUMED":
                self.is_ready.set()

            self.handler.dispatch(_type, data)
        else:
            if op == self.RECONNECT:
                self.close(reconnect=True)

            elif op == self.HELLO:
                self.heartbeat_interval = data['heartbeat_interval']/1000
                self.heartbeat_ready.set()

            elif op == self.INVALID_SESSION:
                if not data:
                    self.session_id = None
                self.close(reconnect=True)

            elif op == self.HEARTBEAT_ACK:
                self.heartbeat_ack.set()

    def heartbeat(self):
        while True:
            limit = time.perf_counter() + self.heartbeat_interval
            if not self.sock.connected:
                logger.debug("Socket disconnected, exiting heartbeat...")
                return
            seq = self.sequence if self.sequence else None
            logger.debug(f"Sending heartbeat with seq {seq}...")
            self.send({
                "op": self.HEARTBEAT,
                "d": seq
            })

            rl = (self.heartbeat_thread._is_stopped, self.heartbeat_ack)
            readable, _, _ = select(rl, (), (), self.heartbeat_interval)
            if self.heartbeat_thread._is_stopped in readable:
                logger.debug("Heartbeat stop requested, exiting heartbeat...")
                return
            elif self.heartbeat_ack not in readable:
                logger.debug("Didn't receive Heartbeat ACK within "
                             f"{self.heartbeat_interval} seconds. "
                             "Reconnecting socket...")
                self.close(reconnect=True, status=STATUS_ABNORMAL_CLOSED)
                return
            elif not readable:
                logger.debug("Socket disconnected, exiting heartbeat...")
                return
            self.heartbeat_ack.clear()
            time.sleep(limit - time.perf_counter())
