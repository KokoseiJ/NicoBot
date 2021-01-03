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

from discordapi.const import VOICE_VER, GATEWAY_CONNECT_TIMEOUT

import json
import time
import socket
import struct
import websocket
import threading
import nacl.secret

IP_DISCOVERY_STRUCT = ">HHI64sH"
VOICE_STRUCT = ">ccHII"


class OggParser:
    def __init__(self, pipe):
        self.pipe = pipe

    def packet_iter(self):
        while True:
            for page in self._page_iter():
                if page is None:
                    yield b""
                    return
                for packet in page:
                    yield packet

    def _page_iter(self):
        magicheader = self.pipe.read(4)
        if magicheader == b"OggS":
            yield self._packet_iter()
        elif not magicheader:
            yield None
            return
        else:
            raise ValueError("Invalid Ogg Header")

    def _packet_iter(self):
        header_struct = struct.Struct("<BBQIIIB")

        version, flag, granule_pos, serial, page_seq, checksum, page_seg = \
            header_struct.unpack(self.pipe.read(header_struct.size))
        seg_table = self.pipe.read(page_seg)

        packet_size = 0

        for table_value in seg_table:
            packet_size += table_value
            if table_value == 255:
                continue
            else:
                packet = self.pipe.read(packet_size)
                packet_size = 0
            yield packet


class VoiceClient:
    def __init__(self, api_endpoint, server_id, user_id, session_id, token):
        if not api_endpoint.startswith("wss://"):
            api_endpoint = f"wss://{api_endpoint}?v={VOICE_VER}"
        self.endpoint = api_endpoint
        self.server_id = server_id
        self.user_id = user_id
        self.session_id = session_id
        self.token = token

        self.heartbeat_interval = None
        self.ssrc = None
        self.server = None
        self.modes = None
        self.secret_key = None
        self.secret_box = None
        self.voice_sequence = 0
        self.timestamp = 0

        self.is_connected = threading.Event()
        self.is_ready = threading.Event()
        self.is_voice_ready = threading.Event()
        self.heartbeat_ack_recieved = threading.Event()
        self.is_close_requested = threading.Event()

        self.run_thread = threading.Thread(target=self._connect,
                                           name="gateway_run")
        self.heartbeat_thread = None

        self.websocket = websocket.WebSocketApp(
            api_endpoint,
            on_open=lambda ws:  threading.Thread(
                target=self._init_gateway,
                args=(ws,),
                name="voice_gateway_init").start(),
            on_message=lambda ws, message:  self._on_message(ws, message)
        )
        self.udp_voice = None

        self.run_thread.start()
        self.is_voice_ready.wait()

    def speak(self):
        self.websocket.send(json.dumps({
            "op": 5,
            "d": {
                "speaking": 1,
                "delay": 0,
                "ssrc": self.ssrc
            }
        }))

    def disconnect(self):
        self.is_close_requested.set()
        self.websocket.close()

    def _connect(self):
        while True:
            print("Connecting to Voice Gateway...")
            self.websocket.run_forever()
            self.is_connected.clear()
            self.is_ready.clear()
            self.heartbeat_ack_recieved.set()
            if self.is_close_requested.is_set():
                break
            print("Connection broken!")

    def _send_voice(self, data):
        header = struct.pack(
            VOICE_STRUCT,
            b"\x80", b"\x78",
            self.voice_sequence,
            self.timestamp,
            self.ssrc
        )
        nonce = bytearray(24)
        nonce[:12] = header
        enc = self.secret_box.encrypt(data, bytes(nonce)).ciphertext
        payload = header + enc
        self.udp_voice.sendto(payload, self.server)
        self.voice_sequence += 1
        self.timestamp += 960

    def _init_gateway(self, ws):
        self.is_connected.wait(timeout=GATEWAY_CONNECT_TIMEOUT)

        ws.send(json.dumps({
            "op": 0,
            "d": {
                "server_id": self.server_id,
                "user_id": self.user_id,
                "session_id": self.session_id,
                "token": self.token
            }
        }))

        print("starting heartbeat")
        self.heartbeat_thread = threading.Thread(
            target=self._heartbeat,
            args=(ws,),
            name="gateway_heartbeat")
        self.heartbeat_thread.start()

        self.is_ready.wait()
        print("READY!")

        print("Running Voice Init")
        self._init_voice(ws)

    def _init_voice(self, ws):
        self.udp_voice = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        addr, port = self._ip_discovery()
        print(addr, port)
        ws.send(json.dumps({
            "op": 1,
            "d": {
                "protocol": "udp",
                "data": {
                    "address": addr,
                    "port": port,
                    "mode": "xsalsa20_poly1305"
                }
            }
        }))
        self.is_voice_ready.wait()
        print("VOICE READY!!")

    def _ip_discovery(self):
        packet = struct.pack(
            IP_DISCOVERY_STRUCT,
            0x1,
            70,
            self.ssrc,
            self.server[0].encode(),
            self.server[1]
        )
        self.udp_voice.sendto(packet, self.server)
        data, addr = self.udp_voice.recvfrom(1024)
        if addr == self.server:
            typ, len, ssrc, addr, port = struct.unpack(
                IP_DISCOVERY_STRUCT, data)
            if not (typ == 0x2 and len == 70 and ssrc == self.ssrc):
                raise RuntimeError("Packet Error")
        addr = addr.replace(b"\x00", b"").decode()
        return addr, port

    def _heartbeat(self, ws):
        while self.is_connected.is_set():
            self.heartbeat_ack_recieved.clear()

            sendtime = time.time()
            ws.send(json.dumps({"op": 3, "d": int(sendtime)}))

            if not self.heartbeat_ack_recieved.wait(self.heartbeat_interval):
                if self.is_connected.is_set():
                    ws.close(websocket.STATUS_ABNORMAL_CLOSED)
                    raise TimeoutError("Timed out while sending heartbeat")
                else:
                    break

            while self.heartbeat_interval > time.time() - sendtime:
                if not self.is_connected.is_set():
                    break
                time.sleep(0.1)
            else:
                continue
            break

    def _on_message(self, ws, message):
        data = json.loads(message)
        print(data)

        if not self.is_connected.is_set():
            if data['op'] == 8:
                self.heartbeat_interval = data['d']['heartbeat_interval']/1000
                self.is_connected.set()
            else:
                raise RuntimeError("Got unexpected response from the server")
        else:
            if data['op'] == 6:
                if not self.heartbeat_ack_recieved.is_set():
                    self.heartbeat_ack_recieved.set()
                else:
                    raise RuntimeError(
                        "Heartbeat ACK received without corresponding request")
            elif data['op'] == 2:
                self.ssrc = data['d']['ssrc']
                self.server = (data['d']['ip'], data['d']['port'])
                self.modes = data['d']['modes']
                self.is_ready.set()
            elif data['op'] == 4:
                self.secret_key = bytes(data['d']['secret_key'])
                print("creating secret box")
                self.secret_box = nacl.secret.SecretBox(self.secret_key)
                print("Ready!")
                self.is_voice_ready.set()
