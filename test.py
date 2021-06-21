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
