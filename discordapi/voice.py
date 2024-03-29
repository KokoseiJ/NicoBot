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

from .const import LIB_NAME
from .exceptions import DiscordError
from .websocket import WebSocketThread

import json
import time
import struct
import socket
import logging
from threading import Event
from websocket import WebSocketException

__all__ = ["DiscordVoiceClient"]

logger = logging.getLogger(LIB_NAME)

IP_DISCOVERY_STRUCT = struct.Struct(">HHI64sH")
VOICE_STRUCT = struct.Struct(">ccHII")

try:
    import nacl.secret

    AVAILABLE = True
except ImportError:
    logger.warning("PyNaCl not found, Voice unavailable")
    AVAILABLE = False


class DiscordVoiceClient(WebSocketThread):
    IDENTIFY = 0
    SELECT_PROTOCOL = 1
    READY = 2
    HEARTBEAT = 3
    SESSION_DESCRIPTION = 4
    SPEAKING = 5
    HEARTBEAT_ACK = 6
    RESUME = 7
    HELLO = 8
    RESUMED = 9
    CLIENT_DISCONNECT = 13

    def __init__(self, client, endpoint, token, session_id, server_id):
        if not AVAILABLE:
            raise DiscordError("PyNaCl not found!")
        super(DiscordVoiceClient, self).__init__(
            endpoint, self._dispatcher, f"voice_{session_id}"
        )

        self.client = client
        self.user_id = client.user.id
        self._set_info(endpoint, token, session_id, server_id)

        self.got_ready = Event()
        self.is_heartbeat_ready = Event()
        self.heartbeat_ack_received = Event()
        self.secret_box = None
        self.voice_sequence = 0
        self.timestamp = 0

        self.heartbeat_interval = None
        self.ssrc = None
        self.server_addr = None
        self.modes = None
        self.ip = None
        self.port = None
        self.secret_key = None

        self.udp_sock = None

    def _set_info(self, endpoint, token, session_id, server_id=None):
        self.url = endpoint
        self.token = token
        self.session_id = session_id
        if server_id is not None:
            self.server_id = server_id

    def reapply_info(self, endpoint, token, session_id, server_id=None):
        logger.info("Applying new information, Reconnecting session...")
        self._set_info(endpoint, token, session_id, server_id)
        self.reconnect(status=1000)

    def get_channel(self):
        guild = self.client.get_guild(self.server_id)
        return guild.voice_states.get(self.client.user.id)

    def speak(self, speaking=1):
        """Send SPEAKING event to the gateway.

        Args:
            speaking:
                either bool or integer. True indicates speaking, False
                indicates that the client is no longer speaking. integer value
                should be the flag value to be used. Default value is 1.
        """
        if speaking is True:
            speaking = 1
        elif speaking is False:
            speaking = 0

        payload = self._get_payload(
            self.SPEAKING, speaking=speaking, delay=0, ssrc=self.ssrc
        )

        try:
            self.send(payload)
        except Exception:
            logger.exception("An exception occured while sending voice data.")

    def disconnect(self):
        self.stop()
        self.client.update_voice_state(self.server_id, None, False, False)

    def _send_voice(self, data):
        header = VOICE_STRUCT.pack(
            b"\x80",
            b"\x78",
            self.voice_sequence % 65536,
            self.timestamp,
            self.ssrc,
        )
        payload = self.xsalsa20_poly1305(header, data)

        self.send_udp(payload)
        self.voice_sequence += 1
        self.timestamp += 960

    def xsalsa20_poly1305(self, header, data):
        nonce = bytearray(24)
        nonce[:12] = header
        enc = self.secret_box.encrypt(data, bytes(nonce)).ciphertext
        return header + enc

    def init_connection(self):
        self.udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.send_identify()
        self.got_ready.wait()
        self.got_ready.clear()

        while True:
            try:
                self.ip, self.port = self.ip_discovery()
                break
            except RuntimeError:
                logger.warning("IP Discovery data mismatch!")
                continue
        self.send_protocol()

    def send_identify(self):
        payload = self._get_payload(
            self.IDENTIFY,
            server_id=self.server_id,
            user_id=self.user_id,
            session_id=self.session_id,
            token=self.token,
        )
        self.send(payload)

    def ip_discovery(self):
        payload = IP_DISCOVERY_STRUCT.pack(
            0x1,
            70,
            self.ssrc,
            self.server_addr[0].encode(),
            self.server_addr[1],
        )

        self.send_udp(payload)

        addr = None
        while addr != self.server_addr:
            payload, addr = self.udp_sock.recvfrom(1024)
        typ, leng, ssrc, addr, port = IP_DISCOVERY_STRUCT.unpack(payload)
        logger.debug(
            f"typ: {typ} leng: {leng} ssrc: {ssrc} addr: {addr} port: {port}"
        )
        if not (typ == 0x2 and leng == 70 and ssrc == self.ssrc):
            raise RuntimeError("Packet Error")

        ip = addr.replace(b"\x00", b"").decode()

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
                "mode": "xsalsa20_poly1305",
            },
        )
        self.send(payload)

    def do_heartbeat(self):
        ready_flag = self.is_heartbeat_ready
        stop_flag = self.heartbeat_thread.stop_flag
        ack_flag = self.heartbeat_ack_received

        ready_flag.wait()

        wait_time = self.heartbeat_interval

        while not stop_flag.is_set():
            ready_flag.wait()
            self.send_heartbeat()
            sendtime = time.time()
            logger.debug("Sending heartbeat...")

            deadline = sendtime + wait_time

            if not ack_flag.wait(deadline - time.time()):
                logger.error("Warning! No HEARTBEAT_ACK received within time!")
                self.reconnect()

            if stop_flag.wait(deadline - time.time()):
                break

            self.heartbeat_ack_received.clear()

        logger.info("Terminating heartbeat thread...")

    def send_heartbeat(self):
        payload = self._get_payload(self.HEARTBEAT, d=time.time())
        try:
            self.send(payload)
        except WebSocketException:
            logger.exception("Exception occured while sending heartbeat.")

    def _get_payload(self, op, d=None, **data):
        return {"op": op, "d": data if d is None else d}

    def cleanup(self):
        self.udp_sock.close()

        self.is_heartbeat_ready.clear()
        self.heartbeat_ack_received.set()

    def _dispatcher(self, data):
        op = data["op"]
        payload = data["d"]

        if op == self.HELLO:
            self.heartbeat_interval = payload["heartbeat_interval"] / 1000
            self.is_heartbeat_ready.set()

        elif op == self.READY:
            self.ssrc = payload["ssrc"]
            self.server_addr = (payload["ip"], payload["port"])
            self.udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.modes = payload["modes"]
            self.got_ready.set()

        elif op == self.SESSION_DESCRIPTION:
            self.secret_key = bytes(payload["secret_key"])
            logger.info("Received secret key, generating SecretBox...")
            self.secret_box = nacl.secret.SecretBox(self.secret_key)
            self.ready_to_run.set()
            logger.info("VOICE READY!!!")

        elif op == self.HEARTBEAT_ACK:
            self.heartbeat_ack_received.set()
