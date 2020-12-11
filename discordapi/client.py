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

from .gateway import DiscordGateway
from .const import INTENTS_DEFAULT, NAME
from .event_handler import GeneratorEventHandler


class DiscordClient:
    def __init__(self, token, intents=INTENTS_DEFAULT,
            handler=GeneratorEventHandler):
        self.token = token
        self.intents = intents

        self.header = {
            "User-Agent": NAME,
            "authorization": f"Bot {self.token}"
        }

        self.event_handler = GeneratorEventHandler(self)

        self.gateway = DiscordGateway(
            token, intents, self.event_handler.handler)
        self.is_ready = self.gateway.is_ready
