from .websocket import WebSocketThread
from .const import LIB_NAME, GATEWAY_URL
from .util import SelectableEvent

import sys
import logging
from select import select

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
        super(WebSocketThread, self).__init__(
            GATEWAY_URL,
            self._dispatcher,
            name
        )
        self.token = token
        self.handler = handler
        self.intents = intents

        self.seq = 0
        self.heartbeat_interval = None
        self.is_heartbeat_ready = SelectableEvent()
        self.heartbeat_ack = SelectableEvent()
        self.is_reconnect = False

    def init_connection(self):
        self.is_heartbeat_ready.wait()
        if not self.is_reconnect:
            self.send_identify()
            self.is_reconnect = True
        else:
            pass

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

    def do_heartbeat(self):
        stop_flag = self.heartbeat_thread.stop_flag
        wait_time = self.heartbeat_interval
        rl, _, _ = select((self.is_heartbeat_ready, stop_flag), (), ())

        while not stop_flag.is_set():
            self.send_heartbeat()

            selectlist = (stop_flag, self.heartbeat_ack)
            rl, _, _ = select(selectlist, (), (), wait_time)

            if stop_flag in rl:
                return
            elif self.heartbeat_ack not in rl:
                logger.error("No HEARTBEAT_ACK received within time!")
                self.ws.close()

    def send_heartbeat(self):
        data = self._get_payload(
            self.HEARTBEAT,
            d=self.seq if self.seq else None
        )
        self.send(data)

    def _get_payload(op, d=None, **data):
        return {
            "op": op,
            "d": data if d is None else d
        }

    def cleanup(self):
        pass

    def _dispatcher(self, data):
        op = data['op']
        payload = data['d']
        seq = data['s']
        event = data['t']

        if op == self.DISPATCH:
            self.seq = seq
            if event == "READY":
                self.user = payload['user']
                self.guilds = payload['guilds']
                self.session_id = payload['session_id']
                self.application = payload['application']
                self.ready_to_run.set()
            elif event == "RESUMED":
                self.ready_to_run.set()
            self.handler.handle(event, payload)

        elif op == self.HELLO:
            self.heartbeat_interval = payload['heartbeat_interval'] / 1000
            self.is_heartbeat_ready.set()

        elif op == self.HEARTBEAT_ACK:
            self.heartbeat_ack.set()
