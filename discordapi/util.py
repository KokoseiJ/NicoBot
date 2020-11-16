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

from discordapi.channel import GuildTextChannel, DMChannel, GuildVoiceChannel,\
                               GroupDMChannel, GuildCategory,\
                               GuildNewsChannel, GuildStoreChannel

__all__ = []


def get_nonesafe(func, args, type=None, alt=None):
    for arg in args:
        if arg is None if type is None else not isinstance(arg, type):
            return alt
    return func(*args)


def get_channel(obj, guild=None):
    type = obj.get("type")
    if type == 0:
        return GuildTextChannel(obj, guild)
    elif type == 1:
        return DMChannel(obj)
    elif type == 2:
        return GuildVoiceChannel(obj, guild)
    elif type == 3:
        return GroupDMChannel(obj)
    elif type == 4:
        return GuildCategory(obj, guild)
    elif type == 5:
        return GuildNewsChannel(obj, guild)
    elif type == 6:
        return GuildStoreChannel(obj, guild)
