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
from sys import platform
from select import select
from websocket import STATUS_ABNORMAL_CLOSED


class DiscordGateway(WebSocketClient):
    """
    Client used to connect to Discord main gateway.

    Attributes:
        token: Discord token to be used when connecting.
        intents: Intents value to be sent. default value is 32509.
        heartbeat_interval: Heartbeat interval received from the server.
        ready_data: Ready data received from the server.
        sequence: sequence number received from the server.
        heartbeat_ready: Event that indicates if heartbeat_interval has been
                         received.
        heartbeat_ack: Event that indicates if the heartbeat ACK has been
                       receieved.
        is_ready: Indicates if Ready data has bee acquired.
    """
    def __init__(self, token, intents=INTENTS_DEFAULT):
        super().__init__(GATEWAY_URL)
        self.token = token
        self.intents = intents

        self.heartbeat_interval = None
        self.ready_data = None
        self.sequence = 0

        self.heartbeat_ready = SelectableEvent()
        self.heartbeat_ack = SelectableEvent()
        self.is_ready = SelectableEvent()

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
        ws.send(json.dumps({
            "op": 2,
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
        if not self.ready_data:
            return self.on_connect(ws)
        self.heartbeat_ready.wait()
        self.run_heartbeat()
        ws.send(json.dumps({
            "op": 6,
            "d": {
                "token": self.token,
                "session_id": self.ready_data['session_id'],
                "seq": self.sequence
            }
        }))

    def on_message(self, data):
        if data['op'] == 10:
            self.heartbeat_interval = data['d']['heartbeat_interval']/1000
            self.heartbeat_ready.set()
        elif data['op'] == 9:
            if not data['d']:
                self.ready_data = None
            self.close(reconnect=True)
        elif data['op'] == 11:
            self.heartbeat_ack.set()
        elif data['op'] == 0:
            _type = data['t']
            event = data['d']
            if _type == "READY":
                self.ready_data = event
                self.is_ready.set()
            elif _type == "RESUMED":
                self.is_ready.set()

    def heartbeat(self):
        while True:
            limit = time.perf_counter() + self.heartbeat_interval
            if not self.sock.connected:
                return
            self.send({
                "op": 1,
                "d": self.sequence if self.sequence else None
            })

            rl = (self.heartbeat_thread._is_stopped, self.heartbeat_ack)
            readable, _, _ = select(rl, (), (), self.heartbeat_interval)
            if self.heartbeat_thread._is_stopped in readable:
                return
            elif not readable:
                self.close(status=STATUS_ABNORMAL_CLOSED)
                return
            self.heartbeat_ack.clear()
            time.sleep(limit - time.perf_counter())
