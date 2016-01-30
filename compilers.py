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

import os
import itertools

from tlib.common import Error, Module
from invoker import Executable


class Language (Module):
    __cache = {}

    def __init__ ( self, *, name=None, binary=None, compiler=None, executable=None, t ):
        super (Language, self).__init__ (t)
        self.__name = name
        self.__binary = binary
        self.__compiler = compiler
        self.__executable = executable
        if binary is None:
            self.__binary = lambda source: source

    def __call__ ( self, source ):
        key = source
        if not key.startswith ('/'):
            key = os.path.join (os.getcwd (), key)
        if key in Language.__cache:
            return Language.__cache[key]
        binary = self.__binary (source)
        need_recompile = True
        if self.__compiler is None:
            Error.ensure (binary == source, "cannot make binary without compiler")
            need_recompile = False
        if os.path.isfile (binary) and os.stat (binary).st_mtime >= os.stat (source).st_mtime:
            need_recompile = False
        if need_recompile:
            self._log ('compile: %s → %s' % (source, binary))
            compiler = Executable (self.__compiler (source, binary), name=self.__name, t=self._t)
            if not compiler (source, binary):
                raise Error ("comilation failed: %s" % source)
        else:
            self._log ('compile skipped: %s' % binary)
        if not binary.startswith ('/'):
            binary = os.path.join (os.getcwd (), binary)
        Language.__cache[key] = self.__executable (binary)
        return Language.__cache[key]


