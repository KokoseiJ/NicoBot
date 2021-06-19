from discordapi.const import LIB_NAME
from discordapi.client import DiscordClient

import sys
import logging
from logging import StreamHandler


def dummy_handler(*args, **kwargs):
    if __name__ == "__main__":
        print(*args)


logger = logging.getLogger(LIB_NAME)
handler = StreamHandler(sys.stdout)

if __name__ != "__main__":
    logger.setLevel("ERROR")
    handler.setLevel("ERROR")
else:
    logger.setLevel("DEBUG")
    handler.setLevel("DEBUG")

fmt = logging.Formatter("[%(levelname)s]|%(asctime)s|%(threadName)s|"
                        "%(funcName)s|: %(message)s")
handler.setFormatter(fmt)
logger.addHandler(handler)

gw = DiscordClient(
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
