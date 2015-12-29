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

import time

class Type:
    def __init__ ( self, t ):
        self._t = t
    def __str__ ( self ):
        assert False
    def dump ( self ):
        assert False
    def __eq__ ( self, x ):
        assert False

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
        data = line.split ()
        if self._time > int(data[0]):
            return None
        event = data[1]
        if event not in self._actions:
            return None
        return True
    def __event ( self, line ):
        data = line.split ()
        self._time = int(data[0])
        event = data[1]
        return self._actions[event] (*data[2:])
    def _commit ( self, *args, check=True ):
        now = str (int (time.time ()))
        line = ' '.join ([now] + list (args))  # TODO: spaces and so on
        if self.__precheck (line) is None:
            assert not check
            return None
        print (line, file=self.__datalog)
        self.__datalog.flush ()
        return self.__event (line)

