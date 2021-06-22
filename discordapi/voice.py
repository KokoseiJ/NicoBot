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

from .const import LIB_NAME, VOICE_VER
from .websocket import WebSocketThread
from .util import SelectableEvent

import json
import time
import select
import struct
import socket
import logging
from websocket import STATUS_ABNORMAL_CLOSED

logger = logging.getLogger(LIB_NAME)

__all__ = []


class DiscordVoiceClient(WebSocketThread):
    IDENTIFY = 0
    SELECT_PROTOCOL = 1
    READY = 2
    HEARTBEAT = 3
    SESSION_DESCRIPTION = 4
    SPEAKING = 5
    HEATBEAT_ACK = 6
    RESUME = 7
    HELLO = 8
    RESUMED = 9
    CLIENT_DISCONNECT = 13

    def __init__(self, client, endpoint, token, session_id, server_id):
        super(DiscordVoiceClient, self).__init__(
            f"wss://{endpoint}?v={VOICE_VER}",
            self._dispatcher,
            f"voice_{session_id}"
        )
        self.client = client
        self.endpoint = f"wss://{endpoint}?v={VOICE_VER}"
        self.token = token
        self.session_id = session_id
        self.server_id = server_id
        self.user_id = client.user.id

        self.heartbeat_interval = None
        self.ssrc = None
        self.server_addr = None
        self.modes = None
        self.ip = None
        self.port = None
        self.key = None
        self.got_ready = SelectableEvent()
        self.is_heartbeat_ready = SelectableEvent()
        self.heartbeat_ack = SelectableEvent()
        self.is_ready = SelectableEvent()

        self.udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def init_connection(self):
        self.send_identify()
        self.got_ready.wait()
        self.got_ready.clear()

        self.ip, self.port = self.ip_discovery()
        self.send_protocol()
        
    def send_identify(self):
        payload = self._get_payload(
            self.IDENTIFY,
            server_id=self.server_id,
            user_id=self.user_id,
            session_id=self.session_id,
            token=self.token
        )
        self.send(payload)

    def ip_discovery(self):
        payload_struct = struct.Struct(">hhI64sH")
        payload = struct.pack(0x1, 70, self.ssrc, b'', 0)
        self.send_udp(self, payload)
        addr = None
        while addr == self.server_addr:
            payload, addr = self.udp_sock.recvfrom(1024)

        data = payload_struct.unpack(payload)

        ip = data[3].decode().rstrip()
        port = data[4]

        return ip, port

    def send_udp(self, data):
        if isinstance(data, dict):
            data = json.dumps(data)
        if isinstance(data, str):
            data = data.encode()

        self.udp_sock.sendto(data, self.server_addr)

    def send_protocol(self):
        payload = self._get_payload(
            self.SELECT_PROTOCOL,
            protocol="udp",
            data={
                "address": self.ip,
                "port": self.port,
                "mode": "xsalsa20_poly1305"
            }
        )
        self.send(payload)

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
                self.ws.close(STATUS_ABNORMAL_CLOSED)

            self.heartbeat_ack.clear()

            rl, _, _ = select((stop_flag,), (), (), deadline - time.time())
            if stop_flag in rl:
                break

        logger.debug("Terminating heartbeat thread...")

    def send_heartbeat(self):
        payload = self._get_payload(
            self.HEARTBEAT,
            d=time.time()
        )
        self.send(payload)

    def _get_payload(self, op, d=None, **data):
        return {
            "op": op,
            "d": data if d is None else d
        }

    def _dispatcher(self, data):
        data = json.loads(data)
        op = data['op']
        payload = data['d']

        if op == self.HELLO:
            self.heartbeat_interval = payload['heartbeat_interval'] / 1000
            self.is_heartbeat_ready.set()

        elif op == self.READY:
            self.ssrc = payload['ssrc']
            self.server_addr = (payload['ip'], payload['port'])
            self.modes = payload['modes']
            self.got_ready.set()

        elif op == self.SESSION_DESCRIPTION:
            self.key = payload['secret_key']

        elif op == self.HEARTBEAT_ACK:
            self.heartbeat_ack.set()
