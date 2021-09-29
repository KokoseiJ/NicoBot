#
# NicoBot is Nicovideo Player bot for Discord, written from the scratch.
# This file is part of NicoBot.
#
# Copyright (C) 2021 Wonjun Jung (KokoseiJ)
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

import os.path

try:
    path = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(path, "..", ".git")
    data = open(os.path.join(path, "HEAD")).read()[5:-1]
    path = os.path.join(path, data)
    data = open(path).read()
    commit = data[:7]
except (FileNotFoundError, IndexError):
    data = None
    path = None
    commit = None

LIB_NAME = "nicobot"
LIB_VER = f"git.{commit}" if commit else "a20210930"
LIB_URL = "https://github.com/KokoseiJ/NicoBot"

GATEWAY_VER = 9
GATEWAY_URL = f"wss://gateway.discord.gg/?v={GATEWAY_VER}&encoding=json"

API_VER = 9
API_URL = f"https://discord.com/api/v{API_VER}/"

VOICE_VER = 4

EMPTY = 1337

del os, path, data, commit
