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

from io import BytesIO
from os.path import split, abspath, exists, isdir


class File:
    """Represents file and name.

    This object could be constructed by either using a traditional constructor
    for simple usages, or using `.from_path`, `.from_io`, `.from_bytes`
    classmethods for explicity. Refer to each methods for detailed usage.

    Attributes:
        name:
            string representing the filename. This could be different from the
            actual file this object is pointing to.
        path:
            An absolute path to the file. This could be None if the instance
            was constructed from BytesIO or bytes, in which case fileobj should
            not be None.
        fileobj:
            io object to the actual file content. This could be None if .read()
            method wasn't called yet- in which case path should not be None.
    """
    def __init__(self, obj=None):
        """Creates File object.

        Args:
            obj:
                This could be str, BytesIO, bytes, bytearray or tuple/list.
                str will be assumed as a path to the file- while other types
                except tuple/list would be used as a file content itself.

                if the type is tuple/list, it should be formatted as following:
                (filename, obj) where filename is str and obj is as explained.

                if the type is BytesIO/bytes/bytearray and filename is not
                given, filename will be defaulted as "file".

        Raises:
            ValueError:
                Raised if the argument doesn't satisfy the requirements.
            FileNotFoundError:
                Raised if obj was str and given path does not exist.
            IsADirectoryError:
                Raised if obj was str and given path was a dir.
        """
        self.name = None
        self.path = None
        self.fileobj = None

        if obj is None:
            return

        name = None

        if isinstance(obj, (list, tuple)):
            try:
                if len(obj) != 2:
                    raise ValueError("Length of the non-str argument "
                                     "should be 2.")
            except TypeError:
                raise ValueError("Argument should be str or "
                                 "tuple/list with 2 items.")
            name, obj = obj

            if not isinstance(name, str):
                raise ValueError("Type of filename should be str, "
                                 f"not '{type(name)}'")

        if isinstance(obj, str):
            self._from_path(obj, name)
            return

        elif name is None:
            name = "file"
        
        if isinstance(obj, BytesIO):
            self._from_io(name, obj)

        elif isinstance(obj, (bytes, bytearray)):
            self._from_bytes(name, obj)

        else:
            raise ValueError(f"Unknown type '{type(obj)}'")

    @classmethod
    def from_path(cls, path, name=None):
        """Creates File object from path.

        args:
            path:
                str object representing the filepath. It can be either relative
                or absolute.
            name:
                str object representing the name.
        Raises:
            ValueError:
                Raised if the argument doesn't satisfy the requirements.
            FileNotFoundError:
                Raised if obj was str and given path does not exist.
            IsADirectoryError:
                Raised if obj was str and given path was a dir.
        """
        if not isinstance(path, str):
            raise ValueError(f"Type of path should be str, not {type(path)}")
        elif not isinstance(name, str):
            raise ValueError(f"Type of name should be str, not {type(name)}")

        instance = cls()
        instance._from_path(path, name)
        return instance

    @classmethod
    def from_io(cls, name, io):
        """Creates File object from io.

        args:
            name:
                str object representing the name.
            io:
                BytesIO object representing the file to read.
        Raises:
            ValueError:
                Raised if the argument doesn't satisfy the requirements.
            FileNotFoundError:
                Raised if obj was str and given path does not exist.
            IsADirectoryError:
                Raised if obj was str and given path was a dir.
        """
        if not isinstance(io, BytesIO):
            raise ValueError(f"Type of path should be BytesIO, not {type(io)}")
        elif not isinstance(name, str):
            raise ValueError(f"Type of name should be str, not {type(name)}")

        instance = cls()
        instance._from_io(name, io)
        return instance

    @classmethod
    def from_bytes(cls, name, byteobj):
        """Creates File object from bytes.

        args:
            name:
                str object representing the name.
            byteobj:
                bytes/bytearray object representing the file to read.
        Raises:
            ValueError:
                Raised if the argument doesn't satisfy the requirements.
            FileNotFoundError:
                Raised if obj was str and given path does not exist.
            IsADirectoryError:
                Raised if obj was str and given path was a dir.
        """
        if not isinstance(byteobj, (bytes, bytearray)):
            raise ValueError("Type of byteobj should be bytes or bytesarray, "
                             f"not {type(byteobj)}")
        elif not isinstance(name, str):
            raise ValueError(f"Type of name should be str, not {type(name)}")

        instance = cls()
        instance._from_bytes(name, byteobj)
        return instance

    def get_name(self):
        return self.name

    def read(self, *args, **kwargs):
        self._prep_read()

        return self.fileobj.read(*args, **kwargs)

    def _prep_read(self):
        if self.fileobj is None:
            if self.path is None:
                raise RuntimeError("Class has not been initialized properly.")
            self.fileobj = open(self.path, "rb")

    def _from_path(self, path, name=None):
        absolute = abspath(path)
        if not exists(absolute):
            raise FileNotFoundError(f"File '{absolute}' does not exist.")
        elif isdir(absolute):
            raise IsADirectoryError(f"'{absolute}' is a directory.")
        self.path = absolute

        if name is None:
            name = split(absolute)[-1]
            if name is None:
                raise NameError("Filename shouldn't be empty???")

        self.name = name

    def _from_io(self, name, obj):
        self.name = name
        self.fileobj = obj

    def _from_bytes(self, name, bytes):
        self.name = name
        self.fileobj = BytesIO(bytes)
