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

from discordapi import LIB_NAME, GATEWAY_URL, GATEWAY_CONNECT_TIMEOUT

import json
import time
import queue
import platform
import threading
import websocket

INTENTS_DEFAULT = 32509


class Gateway:
    def __init__(self, token, event_handler, intents=INTENTS_DEFAULT):
        """
        self.is_connected indicates if connection is available.
        This is used to stop threads when websocket is disconnected.
        self.is_ready indicates if client is in ready status.
        self.heartbeat_ack_recieved indicates if heartbeat ack is recieved.
        self.restart_requested indicates if socket is terminated by interrupt
        or closed socket.
        """
        self.token = token
        self.intents = intents
        self.event_handler = event_handler

        self.heartbeat_interval = None
        self.session_id = None
        self.seq = None
        self.ready_data = None
        self.heartbeat_seq = 0

        self.is_connected = threading.Event()
        self.is_ready = threading.Event()
        self.heartbeat_ack_recieved = threading.Event()
        self.stop_heartbeat = threading.Event()
        self.is_close_requested = threading.Event()

        self.run_thread = threading.Thread(target=self._connect,
                                           name="gateway_run")
        self.heartbeat_thread = None

        self.event_queue = queue.Queue()
        self.guild_list = list()
        self.voice_queue = dict()

        self.websocket = websocket.WebSocketApp(
            GATEWAY_URL,
            on_message=lambda ws, message: self._on_message(ws, message),
            on_open=lambda ws: threading.Thread(
                    target=self._init_gateway,
                    args=(ws,),
                    name="gateway_init").start())

    def connect(self):
        self.run_thread.start()
        self.is_ready.wait()
        return self.run_thread

    def voice_connect(self, guild_id, channel_id, mute=False, deaf=False):
        self.voice_queue[str(guild_id)] = queue.Queue()

        self.websocket.send(json.dumps({
            "op": 4,
            "d": {
                "guild_id": guild_id,
                "channel_id": channel_id,
                "self_mute": mute,
                "self_deaf": deaf
            }
        }))

        voice_state = self.voice_queue[str(guild_id)].get()
        if not (voice_state['op'] == 0 and
                voice_state['t'] == "VOICE_STATE_UPDATE"):
            raise RuntimeError("OPcode is wrong!")

        session_id = voice_state['d']['session_id']

        voice_server = self.voice_queue[str(guild_id)].get()
        if not (voice_server['op'] == 0 and
                voice_server['t'] == "VOICE_SERVER_UPDATE"):
            raise RuntimeError("OPcode is wrong!")

        token = voice_server['d']['token']
        guild_id = voice_server['d']['guild_id']
        endpoint = voice_server['d']['endpoint']

        del self.voice_queue[str(guild_id)]

        return session_id, token, guild_id, endpoint

    def disconnect(self):
        self.is_close_requested.set()
        self.websocket.close()

    def _connect(self):
        while True:
            print("Connecting to Gateway...")
            self.websocket.run_forever()
            self.is_connected.clear()
            self.is_ready.clear()
            self.heartbeat_ack_recieved.set()
            if self.is_close_requested.is_set():
                return
            print("Socket closed. reconnecting...")
            self._reconnect()

    def _reconnect(self):
        self.websocket = websocket.WebSocketApp(
            GATEWAY_URL,
            on_message=lambda ws, message: self._on_message(ws, message),
            on_open=lambda ws: threading.Thread(
                        target=self._resume_gateway,
                        args=(ws,),
                        name="gateway_resume").start())

    def _init_gateway(self, ws):
        self.ws = ws

        if not self.is_connected.wait(timeout=GATEWAY_CONNECT_TIMEOUT):
            raise TimeoutError("Timed out while connecting to Discord Gateway")

        print("starting heartbeat")
        self.heartbeat_thread = threading.Thread(
            target=self._heartbeat,
            name="gateway_heartbeat")
        self.heartbeat_thread.start()

        print("sending auth")
        ws.send(json.dumps({
            "op": 2,
            "d": {
                "token": self.token,
                "intents": self.intents,
                "properties": {
                    "$os": platform.system().lower(),
                    "$browser": LIB_NAME,
                    "$device": LIB_NAME
                }
            }
        }))

        self.is_ready.wait()
        print("READY!")

    def _resume_gateway(self, ws):
        if not self.is_connected.wait(GATEWAY_CONNECT_TIMEOUT):
            raise TimeoutError("Timed out while connecting to Discord Gateway")

        print("sending resume")
        ws.send(json.dumps({
            "op": 6,
            "d": {
                "token": self.token,
                "session_id": self.session_id,
                "seq": self.seq
            }
        }))

        self.is_ready.wait()
        print("READY!")

    def _heartbeat(self):
        self.heartbeat_seq = 0
        while self.is_connected.is_set():
            self.heartbeat_ack_recieved.clear()

            sendtime = time.perf_counter()
            self.websocket.send(json.dumps({
                "op": 1,
                "d": self.heartbeat_seq if self.heartbeat_seq else None
            }))

            if not self.heartbeat_ack_recieved.wait(self.heartbeat_interval):
                if self.is_connected.is_set():
                    self.websocket.close(websocket.STATUS_ABNORMAL_CLOSED)
                    raise TimeoutError("Timed out while sending heartbeat")
                else:
                    break

            time.sleep(sendtime+self.heartbeat_interval - time.perf_counter())
            self.heartbeat_seq += 1

        print("Socket disconnected, stopping heartbeat...")

    def _on_message(self, ws, message):
        data = json.loads(message)

        if not self.is_connected.is_set():
            if data['op'] == 10:
                self.heartbeat_interval = data['d']['heartbeat_interval']/1000
                self.is_connected.set()
            else:
                raise RuntimeError("Got unexpected response from the server")
        else:
            if data['op'] == 11:
                if not self.heartbeat_ack_recieved.is_set():
                    self.heartbeat_ack_recieved.set()
                else:
                    raise RuntimeError(
                        "Heartbeat ACK received without corresponding request")
            elif data['op'] == 0:
                self.seq = data['s']

                if data['t'] == "READY":
                    self.session_id = data['d']['session_id']
                    self.ready_data = data['d']
                    self.is_ready.set()

                elif data['t'] == "RESUMED":
                    self.is_ready.set()

                elif data['t'] in["VOICE_SERVER_UPDATE", "VOICE_STATE_UPDATE"]:
                    self.voice_queue[str(data['d']['guild_id'])].put(data)

                else:
                    if data['t'] == "GUILD_CREATE":
                        self.guild_list.append(data['d'])
                    dat = data['d']
                    typ = data['t']
                    event = (typ, self.event_handler(typ, dat))
                    self.event_queue.put(event)
