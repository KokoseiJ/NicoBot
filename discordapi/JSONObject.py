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

class JSONObject:
    def __init__(self, data, keys=None):
        if keys is not None:
            for key in keys:
                self.__setattr__(key, None)
        for key, val in zip(data.keys(), data.values()):
            self.__setattr__(key, val)

    def _get_repr(self, repr_str, name=None):
        if name is None:
            name = self.__class__.__name__
        return f"<{name} {repr_str}>"

    def __repr__(self):
        name = self.__dict__.get("name")
        return self._get_repr(f"{name if name else ''}({self.id})")
