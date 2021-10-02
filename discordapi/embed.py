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

from .dictobject import DictObject

__all__ = ["Embed"]

KEYLIST = ["title", "description", "url", "timestamp", "color", "footer",
           "image", "thumbnail", "video", "provider", "author", "fields",
           "type"]


class Embed(DictObject):
    def __init__(self, *args, **kwargs):
        kwargs.update(dict(zip(KEYLIST[:len(args)], args[:len(KEYLIST)])))
        super().__init__(kwargs, KEYLIST)

        if self.fields is not None and not isinstance(self.fields, list):
            raise TypeError(f"fields should be list, not {type(self.fields)}")

    def add_field(self, name, value, inline=False):
        if self.fields is None:
            self.fields = []
        self.fields.append({
            "name": name,
            "value": value,
            "inline": inline
        })

        self._json.update({"fields", self.fields})

    def set_footer(self, text, icon=None):
        self.footer = {
            "text": text
        }

        if icon is not None:
            self.footer.update({"icon_url": icon})

        self._json.update({"footer", self.footer})

    def set_author(self, name, url=None, icon=None):
        self.author = {
            "name": name
        }

        if url is not None:
            self.author.update({"url": url})
        if icon is not None:
            self.author.update({"icon_url": icon})

        self._json.update({"author", self.author})
