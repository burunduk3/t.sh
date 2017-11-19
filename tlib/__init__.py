#!/usr/bin/env python3

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


class Error ( Exception ):
    def __init__ ( self, comment=None, *, t ):
        super (Error, self).__init__ (comment)
        self.__t = t

    def log ( self ):
        self.__t.log.fatal (self)


class Module:
    def __init__ ( self, *, t ):
        super (Module, self).__init__ ()
        if isinstance (t, Module):
            self._t = t._t
        else:
            self._t = t

    _log = property (lambda self: self._t.log)
    _run = property (lambda self: self._t.run)
    _error = property (lambda self: self._t.error)
    _ensure = property (lambda self: self._t.ensure)
    _configuration = property (lambda self: self._t.configuration)
    _compilers = property (lambda self: self._t.compilers)


from .log import Color, Log


