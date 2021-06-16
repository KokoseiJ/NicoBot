from .const import LIB_NAME
from .util import StoppableThread, SelectableEvent

import json
import select
import logging
from ssl import SSLError
from websocket import WebSocket


logger = logging.getLogger(LIB_NAME)


class WebSocketThread(StoppableThread):
    def __init__(self, url, handler, name):
        super(StoppableThread, self).__init__()

        self.url = url
        self.sock = None
        self.handler = handler
        self.ready_to_run = SelectableEvent()
        self.name = str(name)

        self.heartbeat_thread = None
        self.init_thread = None

    def run(self):
        self.sock = WebSocket(
            enable_multithread=True,
            skip_utf8_validation=True
        )
        self.run_heartbeat()

        while not self.stop_flag.is_set():
            try:
                self.sock.connect(self.url)
            except Exception:
                logger.exception("Failed to connect to Gateway.")

            self.run_init_connection()

            self._event_loop()

            self.ready_to_run.clear()
            try:
                self.cleanup()
            except Exception:
                logger.exception("Exception occured while cleaning up.")

        self.heartbeat_thread.stop()

    def run_heartbeat(self):
        self.heartbeat_thread = StoppableThread(
            target=self.do_heartbeat,
            name=f"{self.name}_heartbeat"
        )
        self.heartbeat_thread.start()

    def run_init_connection(self):
        self.init_thread = StoppableThread(
            target=self.init_connection,
            name=f"{self.name}_init"
        )
        self.init_thread.start()

    def _event_loop(self):
        while self.sock.is_connected():
            rl, _, _ = select.select((self.sock.sock,), (), ())
            if self.sock.sock not in rl:
                continue
            try:
                data = self.sock.recv()
                if data is None:
                    break
                parsed_data = json.loads(data)
            except json.JSONDecodeError:
                logger.error(f"Gateway returned invalid JSON data:\n{data}")
            except Exception:
                logger.exception(
                    "Exception occured while receiving data from the gateway.")

            try:
                self.handler(parsed_data)
            except Exception:
                logger.exception(
                    "Exception occured while running handler function.")

    def send(self, data):
        if isinstance(data, dict):
            data = json.dumps(data)

        try:
            return self.sock.send(data)
        except SSLError:
            logger.exception("SSLError while sending data! retrying...")
            return self.send(data)

    def is_ready(self):
        return self.ready_to_run.is_set()

    def stop(self):
        super(StoppableThread, self).stop()
        self.sock.close()

    def init_connection(self):
        raise NotImplementedError()

    def do_heartbeat(self):
        raise NotImplementedError()

    def cleanup(self):
        raise NotImplementedError()
