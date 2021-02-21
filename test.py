from discordapi.gateway import DiscordGateway

import sys
import logging

from logging import StreamHandler

logger = logging.getLogger("NicoBot")
logger.setLevel("DEBUG")

handler = StreamHandler(sys.stdout)
handler.setLevel("DEBUG")

fmt = logging.Formatter("[%(levelname)s]|%(asctime)s|%(threadName)s|%(funcName)s|%(message)s")
handler.setFormatter(fmt)
logger.addHandler(handler)

gw = DiscordGateway(open("token").read())
gw.connect()
