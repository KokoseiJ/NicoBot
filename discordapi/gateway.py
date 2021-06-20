from .user import BotUser
from .util import SelectableEvent
from .websocket import WebSocketThread
from .const import LIB_NAME, GATEWAY_URL

import sys
import time
import logging
from select import select
from websocket import STATUS_ABNORMAL_CLOSED

logger = logging.getLogger(LIB_NAME)


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
            },
            presence={
                "activities": [{
                    "name": "Henceforth",
                    "type": 2
                }]
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
                self.ws.close(STATUS_ABNORMAL_CLOSED)

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

    def _dispatcher(self, data):
        op = data['op']
        payload = data['d']
        seq = data['s']
        event = data['t']

        if op == self.DISPATCH:
            self.seq = seq
            if event == "READY":
                self.user = BotUser(payload['user'])
                self.guilds = payload['guilds']
                self.session_id = payload['session_id']
                self.application = payload['application']
                self.ready_to_run.set()
            elif event == "RESUMED":
                self.ready_to_run.set()
            self.event_handler(event, payload)

        elif op == self.INVALID_SESSION:
            self.is_reconnect = payload
            self.sock.close()

        elif op == self.HELLO:
            self.heartbeat_interval = payload['heartbeat_interval'] / 1000
            self.is_heartbeat_ready.set()

        elif op == self.HEARTBEAT_ACK:
            logger.debug("Received Heartbeat ACK!")
            self.heartbeat_ack.set()
