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

import struct

__all__ = []

HEADER_STRUCT = struct.Struct("<BBQIIIB")


class OggParser:
    """Yields packet from the Ogg filestream.
    
    Attributes:
        pipe:
            BytesIO object which has .read method that can read arbitary
            amount of bytes. This is because this class was written with
            ffmpeg stream in mind. To use this class with files, you can just
            pass the file object.
    """
    def __init__(self, pipe):
        self.pipe = pipe

    def packet_iter(self):
        while True:
            for page in self._page_iter():
                if page is None:
                    yield b""
                    return
                for packet in page:
                    yield packet

    def _page_iter(self):
        magicheader = self.pipe.read(4)
        if magicheader == b"OggS":
            yield self._packet_iter()
        elif not magicheader:
            yield None
            return
        else:
            raise ValueError("Invalid Ogg Header")

    def _packet_iter(self):
        version, flag, granule_pos, serial, page_seq, checksum, page_seg = \
            HEADER_STRUCT.unpack(self.pipe.read(HEADER_STRUCT.size))
        seg_table = self.pipe.read(page_seg)

        packet_size = 0

        for table_value in seg_table:
            packet_size += table_value
            if table_value == 255:
                continue
            else:
                packet = self.pipe.read(packet_size)
                packet_size = 0
            yield packet
