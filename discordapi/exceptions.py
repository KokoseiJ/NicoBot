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

__all__ = ["DiscordError", "DiscordHTTPError"]


class DiscordError(Exception):
    '''Base Exception for Discord Errors.
    '''
    pass


class DiscordHTTPError(DiscordError):
    """Exception to be thrown when error occurs from Discord HTTP API.

    Attributes:
        code:
            Error code specified by API.
        message:
            Message specified by API.
        response:
            http.cilent.HTTPResponse object containing the error
    """
    def __init__(self, code, message, response):
        super(DiscordHTTPError, self).__init__(self, code, message, response)
        self.code = code
        self.message = message
        self.response = response

        self.args = (f"{code}: {message}",)
