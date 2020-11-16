# NicoBot - Nicovideo player bot for discord, written from the scratch
# Copyright (C) 2020 Wonjun Jung (Kokosei J)
#
#    This program is free software: you can redistribute it and/or modify
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

VERSION = "0.0.1"
LIB_NAME = "KokoNicoBot"
USER_AGENT = f"{LIB_NAME} {VERSION}"

API_VER = 8
API_URL = f"https://discord.com/api/v{API_VER}/"
GATEWAY_VER = 8
GATEWAY_URL = f"wss://gateway.discord.gg/?v={GATEWAY_VER}&encoding=json"
VOICE_API_VER = 4

GATEWAY_CONNECT_TIMEOUT = 10
