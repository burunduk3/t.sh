#
#    t.py: utility for contest problem development
#    Copyright (C) 2009-2017 Oleg Davydov
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License along
#    with this program; if not, write to the Free Software Foundation, Inc.,
#    51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#

import base64
import re
import struct

from . import common
from .datalog import Type

class String (Type):
    def __init__ ( self, value ):
        self.__value = str (value)

    value = property (lambda self: self.__value)

    def __str__ ( self ):
        return self.__value

    def dump ( self ):
        if re.match ("^[0-9a-zA-Zа-яА-Я\\._+-]+$", self.__value):
            yield self.__value
        else:
            yield '"' + \
                self.__value. \
                replace ('\\', '\\\\').replace ('\n', '\\n').replace ('\t', '\\t'). \
                replace ('\0', '\\0').replace ('\r', '\\r').replace ('"', '\\"') + \
                '"'

    def __eq__ ( self, x ):
        return self.__value == x.__value

    @classmethod
    def parse ( cls, data ):
        return cls (next (data))


class Float (Type):
    def __init__ ( self, value ):
        self.__value = float (value)

    value = property (lambda self: self.__value)

    def __str__ ( self ):
        return '%.20f' % self.__value

    def dump ( self ):
        yield base64.b16encode (struct.pack ('d', self.__value)).decode ('ascii')

    def __eq__ ( self, x ):
        return self.__value == x.__value

    @classmethod
    def parse ( cls, data ):
        value = next (data)
        if re.match ('^[0-9a-f]{16}$', value):
            value = struct.unpack ('d', base64.b16decode (value))[0]
        return cls (value)


class Integer (Type):
    def __init__ ( self, value ):
        self.__value = int (value)

    value = property (lambda self: self.__value)

    def __str__ ( self ):
        return '%d' % self.__value

    def dump ( self ):
        yield str (self.__value)

    def __eq__ ( self, x ):
        return self.__value == x.__value

    @classmethod
    def parse ( cls, data ):
        return cls (next (data))


class Source (Type):
    def __init__ ( self, path, language, languages={} ):
        self.__path = path
        self.__language = language
        self.__languages = languages
        self.__executable = None

    path = property (lambda self: self.__path)
    language = property (lambda self: self.__languages)
    executable = property (lambda self: self.__executable)

    def __str__ ( self ):
        return self.__path

    def dump ( self ):
        yield from String.dumps (self.__path)
        yield from String.dumps (self.__language)

    def __eq__ ( self, other ):
        return type (other) is Source and \
            self.__path == other.__path and \
            self.__language == other.__language

    def compile ( self ):
        compiler = self.__languages[self.__language]
        self.__executable = compiler (self.__path)
        if self.__executable is None:
            raise common.Error ("%s: compilation error" % self.__path)

    def run ( self, *arguments, **kwargs ):
        if self.__executable is None:
            self.compile ()
        return self.__executable (*arguments, **kwargs)

    @classmethod
    def parse ( cls, data, languages={} ):
        path = next (data)
        language = next (data)
        return cls (path, language, languages)

