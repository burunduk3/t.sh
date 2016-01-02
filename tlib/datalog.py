#
#    t.py: utility for contest problem development
#    Copyright (C) 2009-2015 Oleg Davydov
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
import time
import struct


class Type:
    def __init__ ( self, t ):
        self._t = t

    def __str__ ( self ):
        assert False

    def dump ( self ):
        assert False

    def __eq__ ( self, x ):
        assert False


class String (Type):
    def __init__ ( self, value ):
        self.__value = str (value)

    value = property (lambda self: self.__value)

    def __str__ ( self ):
        return self.__value

    def dump ( self ):
        if re.match ("^[0-9a-zA-Zа-яА-Я\\._+-]+$", self.__value):
            return self.__value
        return '"' + \
            self.__value. \
            replace ('\\', '\\\\').replace ('\n', '\\n').replace ('\t', '\\t'). \
            replace ('\0', '\\0').replace ('\r', '\\r').replace ('"', '\\"') + \
            '"'

    def __eq__ ( self, x ):
        return self.__value == x.__value

    # @classmethod
    # def dump ( cls, value ):
    #     return cls (value).dump ()

    @classmethod
    def parse ( cls, value ):
        return cls (value)


class Float (Type):
    def __init__ ( self, value ):
        self.__value = float (value)

    value = property (lambda self: self.__value)

    def __str__ ( self ):
        return '%.20f' % self.__value

    def dump ( self ):
        return base64.b16encode (struct.pack ('d', self.__value)).decode ('ascii')

    def __eq__ ( self, x ):
        return self.__value == x.__value

    @classmethod
    def parse ( cls, value ):
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
        return str (self.__value)

    def __eq__ ( self, x ):
        return self.__value == x.__value

    @classmethod
    def parse ( cls, value ):
        return cls (value)


class Datalog:
    class NotFound (Exception):
        pass

    def __init__ ( self, datalog, actions={}, *, create=False, t ):
        self._t = t
        self._actions = actions
        self._time = 0
        try:
            with open (datalog, 'r') as log:
                for line in log.readlines ():
                    self.__event (line)
        except FileNotFoundError as error:
            if not create:
                raise Datalog.NotFound from error
            self._t.log.warning ("file not found: '%s', create new" % datalog)
        self.__datalog = open (datalog, 'a')

    def __precheck ( self, line ):
        ts, event, data = line.split (' ', 2)
        if self._time > int (ts):
            return None
        if event not in self._actions:
            return None
        return True

    @staticmethod
    def __parse ( line ):
        token = ''

        def state_default ( x ):
            nonlocal token
            if x == ' ' or x == '\n':
                if len (token):
                    yield token
                token = ''
            elif x != '"':
                token += x
            else:
                return state_str
            return state_default

        def state_str ( x ):
            nonlocal token
            if x == '"':
                yield token
                token = ''
                return state_default
            if x == '\\':
                return state_backslash
            token += x
            return state_str

        def state_backslash ( x ):
            nonlocal token
            conv = {'n': '\n', 'r': '\r', 't': '\t', '0': '\0'}
            token += conv.get (x, x)
            return state_str

        state = state_default
        for x in line:
            state = yield from state (x)
        yield from state ('\n')
        assert state is state_default


    def __event ( self, line ):
        ts, event, data = line.split (' ', 2)
        self._time = int (ts)
        return self._actions[event] ( self.__parse (data))

    def _commit ( self, event, *args, check=True ):
        now = str (int (time.time ()))
        line = ' '.join ([now, event] + [x.dump () for x in args])
        if self.__precheck (line) is None:
            assert not check
            return None
        print (line, file=self.__datalog)
        self.__datalog.flush ()
        return self.__event (line)

