from discordapi.handler import Handler
from discordapi.gateway import DiscordGateway

import sys
import logging

from logging import StreamHandler

logger = logging.getLogger("NicoBot")
logger.setLevel("DEBUG")

handler = StreamHandler(sys.stdout)
handler.setLevel("INFO")

fmt = logging.Formatter("[%(levelname)s]|%(asctime)s|%(threadName)s|"
                        "%(funcName)s|: %(message)s")
handler.setFormatter(fmt)
logger.addHandler(handler)


class TestHandler(Handler):
    def on_message_create(self, event):
        logger.info(f"{event['author']['username']}#"
                    f"{event['author']['discriminator']}: {event['content']}")


gw = DiscordGateway(open("token").read(), TestHandler)

try:
    gw.connect()
except KeyboardInterrupt:
    gw.close()
