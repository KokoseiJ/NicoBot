from discordapi.const import LIB_NAME
from discordapi.gateway import DiscordGateway

import sys
import logging
from logging import StreamHandler


def dummy_handler(*args, **kwargs):
    print(*args)
    pass


logger = logging.getLogger(LIB_NAME)
logger.setLevel("DEBUG")

handler = StreamHandler(sys.stdout)
handler.setLevel("DEBUG")

fmt = logging.Formatter("[%(levelname)s]|%(asctime)s|%(threadName)s|"
                        "%(funcName)s|: %(message)s")
handler.setFormatter(fmt)
logger.addHandler(handler)

gw = DiscordGateway(
    open("token").read(),
    dummy_handler
)

gw.start()


if __name__ == "__main__":
    try:
        gw.join()
    except KeyboardInterrupt:
        print("OUCH THAT HURTS")
    finally:
        gw.stop()
        gw.join()

    print("exiting")
