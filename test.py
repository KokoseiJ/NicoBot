from discordapi.const import LIB_NAME
from discordapi.gateway import DiscordGateway

import logging


def dummy_handler(*args, **kwargs):
    print(*args)
    pass


logger = logging.getLogger(LIB_NAME)
logger.setLevel(logging.DEBUG)

ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

ch.setFormatter(
    logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
)

logger.addHandler(ch)

gw = DiscordGateway(
    open("token").read(),
    dummy_handler
)

gw.start()


try:
    gw.join()
except KeyboardInterrupt:
    print("OUCH THAT HURTS")
finally:
    gw.stop()
    gw.join()

print("exiting")
