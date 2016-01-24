#
#    t.py: utility for contest problem development
#    Copyright (C) 2009-2016 Oleg Davydov
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

import itertools
import time

from . import common


class Type:
    def __init__ ( self, t ):
        self._t = t

    def __str__ ( self ):
        assert False

    def dump ( self ):
        assert False

    def __eq__ ( self, x ):
        assert False

    @classmethod
    def dumps ( cls, value ):
        yield from cls (value).dump ()


class Datalog (common.Module):
    class NotFound (Exception):
        pass

    # use write=True to save data in memory, readonly=True for deny any change
    def __init__ ( self, datalog, actions={}, *, create=False, write=True, readonly=False, t ):
        super (Datalog, self).__init__ (t)
        self._actions = actions
        self._time = 0
        self.__readonly = readonly
        if self.__readonly:
            write = False
        try:
            with open (datalog, 'r') as log:
                for line in log.readlines ():
                    self.__event (line.strip ())
        except FileNotFoundError as error:
            if create:
                assert (write)
                self._t.log.warning ("file not found: '%s', create new" % datalog)
            elif write:
                raise Datalog.NotFound from error
        if write:
            self.__datalog = open (datalog, 'a')
        else:
            self.__datalog = None

    def _upgrade ( self, key, action ):
        assert key not in self._actions
        self._actions[key] = action

    def __precheck ( self, line ):
        ts, event, *data = line.split (' ', 2)
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
        ts, event, *data = line.split (' ', 2)
        if len (data):
            data = data[0]
        else:
            data = ''
        self._time = int (ts)
        return self._actions[event] ( self.__parse (data))

    @staticmethod
    def __logevent ( now, event, *args ):
       yield now
       yield event
       for x in args:
           for y in x.dump ():
               yield y

    def _commit ( self, event, *args, check=True ):
        assert not self.__readonly
        now = str (int (time.time ()))
        line = ' '.join (self.__logevent (now, event, *args))
        if self.__precheck (line) is None:
            assert not check
            return None
        if self.__datalog is not None:
            print (line, file=self.__datalog)
            self.__datalog.flush ()
        return self.__event (line.strip ())

