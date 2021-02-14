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
        sequence: sequence number received from the server.
        heartbeat_interval: Heartbeat interval received from the server.
    """
    def __init__(self, token, intents=INTENTS_DEFAULT):
        super().__init__(GATEWAY_URL)
        self.token = token
        self.intents = intents

        self.sequence = 0
        self.heartbeat_interval = None

        self.heartbeat_ack = SelectableEvent()

    def on_connect(self, ws):
        raw = ws.recv()
        data = json.loads(raw)
        if data['op'] != 10:
            raise RuntimeError(f"Unexpected response.\npayload: {raw}")
        self.heartbeat_interval = data['d']['heartbeat_interval'] / 1000
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
        print(ws.recv())
        print(ws.recv())
        self.close()

    def heartbeat(self):
        while True:
            limit = time.perf_counter() + self.heartbeat_interval
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
            time.sleep(limit - time.perf_counter())
