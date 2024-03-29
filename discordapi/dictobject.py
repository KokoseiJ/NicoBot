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

__all__ = ["DictObject"]


class DictObject:
    """Object which automatically sets the attribute based on a dict object.

    Attributes:
        _json:
            The original dict object in which the class was constructed from.
    """

    def __init__(self, data, keylist=[]):
        """Constructs the class from the data.

        This automatically sets the attributes from the dict. additionally,
        keys in keylist will be set as an attribute with the value of None
        when the attribute doesn't exist- this is to ensure that it won't
        overwrite the existing keys when running __init__ in already
        initialized instance.
        """
        self._json = data

        for key in keylist:
            value = data.get(key)
            if value is not None:
                setattr(self, key, value)
            elif getattr(self, key, None) is None:
                setattr(self, key, None)

    def _get_str(self, class_, id_, repr_=None):
        if repr_ is not None:
            return f"<{class_} '{repr_}' ({id_})>"
        else:
            return f"<{class_} ({id_})>"

    def __str__(self):
        class_name = self.__class__.__name__
        return self._get_str(class_name, self.id, self.name)

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        if (
            getattr(self, "id", None) is not None
            and getattr(other, "id", None) is not None
        ):
            return self.id == other.id
        else:
            return False
